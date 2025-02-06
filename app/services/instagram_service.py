from instagrapi import Client
from instagrapi.mixins.challenge import ChallengeChoice
from datetime import datetime, timedelta, timezone
from ..models.social_post import SocialPost
from ..config.settings import get_settings, get_keywords
from .matchers.base_matcher import BaseMatcher
from .matchers.question_matcher import QuestionMatcher
from typing import List, Tuple
import logging
import asyncio
import imaplib
import email
import re
import random
import json
import os

logger = logging.getLogger("uvicorn")

class InstagramService:
    def __init__(self):
        logger.info("Initializing InstagramService")
        self.settings = get_settings()
        self.keywords = get_keywords()["instagram"]
        self.session_file = "instagram_session.json"
        self.client = self._initialize_client()

    def _change_password_handler(self, username):
        """Handle Instagram's password change challenge"""
        # Generate a new password with specific requirements
        chars = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*")
        password = "".join(random.sample(chars, 12))  # 12 character password
        logger.info(f"Generated new password for {username}")
        return password

    def _get_code_from_email(self, username):
        """Get verification code from Gmail"""
        try:
            # Connect to Gmail IMAP
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            mail.login(self.settings.INSTAGRAM_EMAIL, self.settings.INSTAGRAM_EMAIL_PASSWORD)
            mail.select("inbox")
            
            # Search for recent unread emails from Instagram
            result, data = mail.search(None, '(UNSEEN FROM "security@mail.instagram.com")')
            if result != "OK":
                logger.error(f"Error searching emails: {result}")
                return False

            ids = data[0].split()
            for num in reversed(ids):  # Get most recent first
                # Mark as read
                mail.store(num, "+FLAGS", "\\Seen")
                result, data = mail.fetch(num, "(RFC822)")
                if result != "OK":
                    continue

                msg = email.message_from_bytes(data[0][1])
                
                # Handle multipart messages
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            body = part.get_payload(decode=True).decode()
                            # Look for 6-digit code
                            match = re.search(r">(\d{6})<", body)
                            if match:
                                code = match.group(1)
                                logger.info(f"Found verification code: {code}")
                                return code
                else:
                    body = msg.get_payload(decode=True).decode()
                    match = re.search(r">(\d{6})<", body)
                    if match:
                        code = match.group(1)
                        logger.info(f"Found verification code: {code}")
                        return code

            logger.error("No verification code found in emails")
            return False

        except Exception as e:
            logger.error(f"Error getting code from email: {str(e)}")
            return False

    def _challenge_code_handler(self, username, choice):
        """Handle Instagram's verification code challenge"""
        if choice == ChallengeChoice.EMAIL:
            return self._get_code_from_email(username)
        return False

    def _initialize_client(self) -> Client:
        """Initialize Instagram client with credentials and challenge handlers"""
        try:
            client = Client()
            # Set up challenge handlers
            client.challenge_code_handler = self._challenge_code_handler
            client.change_password_handler = self._change_password_handler
            
            # Try to load existing session
            if os.path.exists(self.session_file):
                try:
                    logger.info("Loading existing Instagram session")
                    with open(self.session_file) as f:
                        cached_settings = json.load(f)
                    client.set_settings(cached_settings)
                    # Verify the session is still valid
                    client.get_timeline_feed()
                    logger.info("Successfully restored Instagram session")
                    return client
                except Exception as e:
                    logger.warning(f"Failed to restore session: {str(e)}")
                    # If session is invalid, remove the file
                    os.remove(self.session_file)
            
            # If no valid session exists, perform fresh login
            logger.info("Performing fresh Instagram login")
            client.login(
                self.settings.INSTAGRAM_USERNAME,
                self.settings.INSTAGRAM_PASSWORD
            )
            
            # Save the new session
            with open(self.session_file, 'w') as f:
                json.dump(client.get_settings(), f)
            logger.info("Saved new Instagram session")
            
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Instagram client: {str(e)}")
            raise

    def _normalize_post(self, comment, media, matched_keyword: str) -> SocialPost:
        """Convert Instagram comment to normalized SocialPost model"""
        return SocialPost(
            platform="instagram",
            content=comment.text,
            title=None,
            author=comment.user.username,
            url=f"https://instagram.com/p/{media.code}",
            timestamp=comment.created_at_utc.replace(tzinfo=timezone.utc),
            keyword_matched=matched_keyword,
            community=None,
            likes=comment.like_count
        )

    async def get_matching_posts(self) -> List[SocialPost]:
        """Get comments from configured accounts' reels matching keywords"""
        matching_posts = []
        scan_cutoff = datetime.now(timezone.utc) - timedelta(minutes=self.settings.SCAN_INTERVAL_MINUTES)
        logger.info(f"Starting Instagram reels scan, cutoff time: {scan_cutoff}")

        # Statistics tracking
        total_reels_processed = 0
        reels_with_comments = 0
        total_comments_processed = 0
        total_matching_comments = 0

        try:
            accounts = list(self.keywords["accounts"])
            random.shuffle(accounts)
            
            for username in accounts:
                logger.info(f"\n{'='*50}\nScanning account: {username}\n{'='*50}")
                
                try:
                    await asyncio.sleep(random.uniform(3, 6))
                    try:
                        user_id = self.client.user_id_from_username(username)
                    except Exception as e:
                        if "login_required" in str(e).lower():
                            logger.warning("Session expired during scan, attempting to re-authenticate")
                            self.client = self._initialize_client()
                            user_id = self.client.user_id_from_username(username)
                        else:
                            raise
                    
                    logger.info(f"Got user_id {user_id} for {username}")
                    
                    await asyncio.sleep(random.uniform(2, 4))
                    reels_amount = random.randint(10, 15)
                    try:
                        medias = list(self.client.user_clips(user_id, amount=reels_amount))
                    except Exception as e:
                        if "login_required" in str(e).lower():
                            logger.warning("Session expired during scan, attempting to re-authenticate")
                            self.client = self._initialize_client()
                            medias = list(self.client.user_clips(user_id, amount=reels_amount))
                        else:
                            raise
                            
                    logger.info(f"Fetched {len(medias)} reels for {username}")
                    
                    if not medias:
                        continue
                        
                    random.shuffle(medias)
                    
                    for media in medias:
                        total_reels_processed += 1
                        logger.info(f"\n{'-'*30}\nProcessing reel {media.code}\n{'-'*30}")
                        
                        await asyncio.sleep(random.uniform(2, 4))
                        
                        try:
                            # Check if reel has comments first
                            try:
                                media_info = self.client.media_info(media.id)
                            except Exception as e:
                                if "login_required" in str(e).lower():
                                    logger.warning("Session expired during scan, attempting to re-authenticate")
                                    self.client = self._initialize_client()
                                    media_info = self.client.media_info(media.id)
                                else:
                                    raise
                                    
                            comment_count = getattr(media_info, 'comment_count', 0)
                            
                            logger.info(f"Comment count from media_info: {comment_count}")
                            
                            if comment_count == 0:
                                logger.info(f"Skipping reel {media.code} - no comments")
                                continue
                                
                            logger.info(f"Reel {media.code} has {comment_count} comments")
                            reels_with_comments += 1
                            
                            await asyncio.sleep(random.uniform(2, 4))
                            
                            # Fetch comments with pagination
                            comments = []
                            next_min_id = None
                            chunk_size = random.randint(20, 30)
                            found_old_comments = False
                            
                            while True:
                                logger.info(f"Fetching comments chunk (size={chunk_size}, min_id={next_min_id})")
                                try:
                                    comments_chunk, next_min_id = self.client.media_comments_chunk(
                                        media.id,
                                        max_amount=chunk_size,
                                        min_id=next_min_id
                                    )
                                except Exception as e:
                                    if "login_required" in str(e).lower():
                                        logger.warning("Session expired during scan, attempting to re-authenticate")
                                        self.client = self._initialize_client()
                                        comments_chunk, next_min_id = self.client.media_comments_chunk(
                                            media.id,
                                            max_amount=chunk_size,
                                            min_id=next_min_id
                                        )
                                    else:
                                        raise
                                        
                                chunk_comments = list(comments_chunk)
                                logger.info(f"Retrieved {len(chunk_comments)} comments in this chunk")
                                
                                if chunk_comments:
                                    logger.info(f"Sample comment: {chunk_comments[0].text[:100]}")
                                    logger.info(f"First comment timestamp: {chunk_comments[0].created_at_utc}")
                                    if len(chunk_comments) > 1:
                                        logger.info(f"Last comment timestamp: {chunk_comments[-1].created_at_utc}")
                                
                                # Check if we've hit comments older than our cutoff
                                if chunk_comments and chunk_comments[-1].created_at_utc.replace(tzinfo=timezone.utc) < scan_cutoff:
                                    # Filter out comments older than cutoff
                                    chunk_comments = [c for c in chunk_comments 
                                                    if c.created_at_utc.replace(tzinfo=timezone.utc) >= scan_cutoff]
                                    logger.info(f"Filtered to {len(chunk_comments)} comments within cutoff time")
                                    comments.extend(chunk_comments)
                                    found_old_comments = True
                                    break
                                
                                comments.extend(chunk_comments)
                                
                                if not next_min_id or found_old_comments:
                                    logger.info("No more comments to fetch")
                                    break
                                    
                                await asyncio.sleep(random.uniform(3, 5))
                            
                            total_comments_processed += len(comments)
                            logger.info(f"Processing {len(comments)} total comments for this reel")
                            
                            # Randomize comment processing order
                            random.shuffle(comments)
                            
                            for comment in comments:
                                logger.info(f"Processing comment: {comment.text[:100]}")
                                matches, keyword = self._match_content(comment.text)
                                if matches:
                                    matching_posts.append(
                                        self._normalize_post(comment, media, keyword)
                                    )
                                    total_matching_comments += 1
                                    logger.info(f"Match found! Keyword: '{keyword}' - Text: {comment.text[:100]}")
                            
                        except Exception as e:
                            logger.error(f"Error processing reel {media.code}: {str(e)}")
                            continue

                except Exception as e:
                    logger.error(f"Error scanning account {username}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in Instagram scan: {str(e)}")
            raise

        # Log final statistics
        logger.info(f"\n{'='*50}\nInstagram Scan Statistics:\n{'='*50}")
        logger.info(f"Total reels processed: {total_reels_processed}")
        logger.info(f"Reels with comments: {reels_with_comments}")
        logger.info(f"Total comments processed: {total_comments_processed}")
        logger.info(f"Total matching comments found: {total_matching_comments}")
        logger.info(f"Scan complete. Found {len(matching_posts)} matching posts\n{'='*50}")
        
        return matching_posts

    def _match_content(self, text: str) -> Tuple[bool, str]:
        """Match content against keywords and patterns"""
        # Try base keyword matching first
        matches, keyword = BaseMatcher.match(text, self.keywords)
        if matches:
            logger.info(f"Found matching keyword: {keyword}")
            return True, keyword
        
        # Try question matching
        matches, pattern = QuestionMatcher.match(text, self.keywords)
        if matches:
            logger.info(f"Found matching question pattern: {pattern}")
            return True, pattern
        
        return False, "" 