# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import sys
import json
import os
import traceback
import argparse
import random

DEFAULT_SITES = []

# Control variable to determine if multi-page button click sequence should be executed
EXECUTE_MULTI_PAGE_UPDATE = False

# Configuration variables
LOGIN_WAIT_TIME = 15  # Seconds to wait for login completion (increased from 5)
SITE_INTERVAL_TIME = 20  # Seconds to wait between sites (increased from 5)
LOGIN_RETRY_COUNT = 3  # Maximum number of login retry attempts
DEPLOYMENT_WAIT_TIME = 45  # Seconds to wait for deployment status (increased from 30)

def take_screenshot(driver, name):
    """Empty function, does not take screenshots"""
    # Screenshot functionality disabled
    return None

def wait_and_click(driver, selector, by=By.CSS_SELECTOR, timeout=10, description="element"):
    """Wait for element to appear and click it with retries and detailed logs"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )
        print(f"Found {description}, attempting to click...")
        
        try:
            # Try using JavaScript to click
            driver.execute_script("arguments[0].click();", element)
            print(f"Successfully clicked {description} using JavaScript")
            return True
        except Exception as js_error:
            print(f"JavaScript click failed: {js_error}")
            try:
                # Try regular click
                element.click()
                print(f"Successfully clicked {description} using regular method")
                return True
            except Exception as click_error:
                print(f"Regular click failed: {click_error}")
                return False
    except TimeoutException:
        print(f"Timeout waiting for {description}")
        return False
    except Exception as e:
        print(f"Error waiting/clicking {description}: {e}")
        return False

def handle_confirmation_dialog(driver):
    """Handle confirmation dialog, click 'Sure' button"""
    confirmation_clicked = False
    
    # Try three times
    for attempt in range(3):
        if confirmation_clicked:
            break
            
        print(f"Trying to find and click confirmation button (attempt {attempt+1}/3)...")
        
        try:
            # Get HTML of all dialogs on the page for debugging
            page_html = driver.page_source
            dialog_html = ""
            
            dialogs = driver.find_elements(By.CSS_SELECTOR, ".el-message-box, .el-dialog, .modal, .dialog, [role='dialog']")
            print(f"Found {len(dialogs)} possible dialogs")
            
            for i, dialog in enumerate(dialogs):
                try:
                    dialog_html += f"\nDialog {i+1} HTML: {dialog.get_attribute('outerHTML')}"
                    
                    # Check if dialog is visible
                    if not dialog.is_displayed():
                        print(f"Dialog {i+1} not visible, skipping")
                        continue
                        
                    print(f"Analyzing dialog {i+1}, text: {dialog.text}")
                    
                    # If dialog contains "confirm update" text
                    if "确认更新" in dialog.text or "确认" in dialog.text:
                        print(f"Dialog {i+1} contains confirmation text")
                        
                        # Find all buttons
                        buttons = dialog.find_elements(By.TAG_NAME, "button")
                        print(f"Found {len(buttons)} buttons in dialog")
                        
                        # Go through all buttons
                        for j, button in enumerate(buttons):
                            try:
                                button_text = button.text.strip().lower()
                                print(f"Button {j+1} text: '{button_text}'")
                                
                                if any(text in button_text for text in ['sure', 'yes', 'ok', '确认', 'confirm']):
                                    print(f"Found confirmation button: '{button_text}'")
                                    
                                    try:
                                        # Use JavaScript to click
                                        driver.execute_script("arguments[0].click();", button)
                                        print("Clicked confirmation button using JavaScript")
                                        confirmation_clicked = True
                                        time.sleep(1)
                                        break
                                    except Exception as js_error:
                                        print(f"JavaScript click failed: {js_error}")
                                        try:
                                            # Try regular click
                                            button.click()
                                            print("Clicked confirmation button using regular method")
                                            confirmation_clicked = True
                                            time.sleep(1)
                                            break
                                        except Exception as click_error:
                                            print(f"Regular click on confirmation button failed: {click_error}")
                            except Exception as button_error:
                                print(f"Error processing button {j+1}: {button_error}")
                        
                        # If click successful, break out of dialog loop
                        if confirmation_clicked:
                            break
                except Exception as dialog_error:
                    print(f"Error processing dialog {i+1}: {dialog_error}")
            
            # If no button found through dialogs, try direct button search
            if not confirmation_clicked:
                print("No confirmation button found via dialogs, trying direct search...")
                
                # Try multiple selectors
                selectors = [
                    "//button[contains(., 'Sure')]",
                    "//button[contains(., 'sure')]",
                    "//button[contains(., '确认')]",
                    "//button[contains(., 'Yes')]",
                    "//button[contains(., 'OK')]",
                    "//button[contains(., 'Confirm')]",
                    ".el-button--primary",  # Element UI primary button
                    ".btn-primary",          # Bootstrap primary button
                    ".confirm-btn"           # Common confirmation button class
                ]
                
                for selector in selectors:
                    try:
                        selector_type = By.XPATH if selector.startswith("//") else By.CSS_SELECTOR
                        buttons = driver.find_elements(selector_type, selector)
                        
                        print(f"Selector '{selector}' found {len(buttons)} buttons")
                        
                        for j, button in enumerate(buttons):
                            if button.is_displayed() and button.is_enabled():
                                try:
                                    print(f"Trying to click button: {button.text}")
                                    driver.execute_script("arguments[0].click();", button)
                                    print(f"Clicked button using JavaScript")
                                    confirmation_clicked = True
                                    time.sleep(1)
                                    break
                                except Exception as js_error:
                                    print(f"JavaScript click failed: {js_error}")
                                    try:
                                        button.click()
                                        print(f"Clicked button using regular method")
                                        confirmation_clicked = True
                                        time.sleep(1)
                                        break
                                    except Exception as click_error:
                                        print(f"Regular click failed: {click_error}")
                        
                        if confirmation_clicked:
                            break
                    except Exception as selector_error:
                        print(f"Error using selector '{selector}': {selector_error}")
            
            # Save debug info for current attempt
            if not confirmation_clicked:
                print("Current attempt did not find confirmation button")
                print(f"Page dialog HTML: {dialog_html}")
        
        except Exception as attempt_error:
            print(f"Error in attempt {attempt+1} to find confirmation button: {attempt_error}")
            traceback.print_exc()
        
        # If not clicked and more attempts left, wait and try again
        if not confirmation_clicked and attempt < 2:
            print(f"Waiting 2 seconds before next attempt...")
            time.sleep(2)
    
    return confirmation_clicked

def check_deployment_status(driver, site_url):
    """Check deployment status, returns True (success), False (failure) or None (unknown)"""
    # Wait longer for deployment status indicators
    max_wait_time = DEPLOYMENT_WAIT_TIME  # Increased from 30 to 45 seconds
    start_time = time.time()
    deployment_status_found = False
    
    while time.time() - start_time < max_wait_time and not deployment_status_found:
        try:
            # Check for deployment failure (.blog-login element)
            login_elements = driver.find_elements(By.CSS_SELECTOR, ".blog-login")
            if login_elements and any(element.is_displayed() for element in login_elements):
                print("\n===================================")
                print(f"[X] Site {site_url} deployment failed! System may have logged out.")
                print("===================================\n")
                deployment_status_found = True
                return False
            
            # Check for deployment success (.el-message--success element)
            success_elements = driver.find_elements(By.CSS_SELECTOR, ".el-message--success")
            if success_elements and any(element.is_displayed() for element in success_elements):
                print("\n===================================")
                print(f"[+] Site {site_url} deployed successfully! Styles updated.")
                print("===================================\n")
                deployment_status_found = True
                return True
            
            # Extended check: look for any elements that might indicate success
            success_indicators = driver.find_elements(By.CSS_SELECTOR, ".success, .alert-success, .text-success")
            if success_indicators and any(element.is_displayed() for element in success_indicators):
                print("\n===================================")
                print(f"[+] Site {site_url} appears to have deployed successfully! Found success indicator.")
                print("===================================\n")
                deployment_status_found = True
                return True
                
            # Wait a bit before checking again
            time.sleep(1)
            print(f"Waiting for deployment status... Waited {int(time.time() - start_time)} seconds", end="\r")
        except Exception as e:
            print(f"Error checking deployment status: {e}")
            time.sleep(1)
    
    if not deployment_status_found:
        print("\n===================================")
        print(f"[!] Site {site_url} deployment status unknown! Timeout, please check manually.")
        print("===================================\n")
        return None
    
    return None

def click_button_with_confirmation(driver, button_text, site_url):
    """Click a button with specified text, handle confirmation dialog, and check deployment status"""
    try:
        print(f"\n----- Attempting to click button: '{button_text}' -----")
        
        # Try to find the button
        button_found = False
        
        # Method 1: Find button by XPath containing text
        try:
            button_xpath = f"//button[contains(., '{button_text}')]"
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, button_xpath))
            )
            button_found = True
            print(f"Found button: '{button_text}' (XPath)")
        except:
            print(f"Button not found via XPath: '{button_text}'")
        
        # Method 2: Iterate through all buttons
        if not button_found:
            print("Trying to iterate through all buttons...")
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                try:
                    if button_text in btn.text and btn.is_displayed():
                        button = btn
                        button_found = True
                        print(f"Found button: '{button_text}' (iteration)")
                        break
                except:
                    continue
        
        if not button_found:
            print(f"Button not found: '{button_text}'")
            return False
        
        # Click the button
        try:
            driver.execute_script("arguments[0].click();", button)
            print(f"Clicked button using JavaScript: '{button_text}'")
        except:
            try:
                button.click()
                print(f"Clicked button using regular method: '{button_text}'")
            except Exception as click_error:
                print(f"Failed to click button '{button_text}': {click_error}")
                return False
        
        # Wait for confirmation dialog to appear
        print("Waiting for confirmation dialog...")
        time.sleep(2)
        
        # Handle confirmation dialog
        confirmation_clicked = handle_confirmation_dialog(driver)
        
        if not confirmation_clicked:
            print(f"\n===================================")
            print(f"[!] Unable to click confirmation button, '{button_text}' may not have executed.")
            print("===================================\n")
            return False
        
        # Check deployment status
        print(f"Checking '{button_text}' deployment status...")
        deployment_result = check_deployment_status(driver, site_url)
        
        if deployment_result is False:
            # Deployment failed, return failure
            return False
        
        # Deployment succeeded or status unknown, continue
        return True
        
    except Exception as e:
        print(f"Error during button click process '{button_text}': {e}")
        traceback.print_exc()
        return False

def perform_multi_page_updates(driver, base_url):
    """Perform multi-page button click update operations"""
    if not EXECUTE_MULTI_PAGE_UPDATE:
        print("\nMulti-page update feature is disabled. To enable, set EXECUTE_MULTI_PAGE_UPDATE = False\n")
        return True
    
    print("\n===== Beginning multi-page update operations =====\n")
    
    try:
        # 1. Article list page - aritcle-list
        article_page = f"{base_url}/frontend/page/aritcle-list"
        print(f"\n[1/3] Visiting article list page: {article_page}")
        driver.get(article_page)
        time.sleep(3)
        
        # Click buttons in sequence
        article_buttons = ["更新公共样式", "更新blog全部列表", "更新blog全部详情"]
        for btn_text in article_buttons:
            if not click_button_with_confirmation(driver, btn_text, article_page):
                print(f"\n[X] Failed to click '{btn_text}' on article page, aborting operation")
                return False
            time.sleep(2)  # Wait between buttons
        
        # 2. FAQ list page - faq-list
        faq_page = f"{base_url}/frontend/page/faq-list"
        print(f"\n[2/3] Visiting FAQ list page: {faq_page}")
        driver.get(faq_page)
        time.sleep(3)
        
        # Click buttons in sequence
        faq_buttons = ["更新公共样式", "更新faq全部列表", "更新faq全部详情"]
        for btn_text in faq_buttons:
            if not click_button_with_confirmation(driver, btn_text, faq_page):
                print(f"\n[X] Failed to click '{btn_text}' on FAQ page, aborting operation")
                return False
            time.sleep(2)  # Wait between buttons
        
        # 3. News page - pressroom-list (may not exist)
        pressroom_page = f"{base_url}/frontend/page/pressroom-list"
        print(f"\n[3/3] Attempting to visit news page: {pressroom_page}")
        
        # Check if page exists
        try:
            driver.get(pressroom_page)
            time.sleep(3)
            
            # Check if page loaded expected content
            try:
                # Try to find at least one button to confirm page is correctly loaded
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(., '更新公共样式')]"))
                )
                print("News page exists, continuing execution")
                
                # Click buttons in sequence
                pressroom_buttons = ["更新公共样式", "更新pressroom全部列表", "更新pressroom全部详情"]
                for btn_text in pressroom_buttons:
                    if not click_button_with_confirmation(driver, btn_text, pressroom_page):
                        print(f"\n[X] Failed to click '{btn_text}' on news page, aborting operation")
                        return False
                    time.sleep(2)  # Wait between buttons
                
            except (TimeoutException, NoSuchElementException):
                print("News page doesn't exist or expected button not found, skipping this page")
        
        except Exception as e:
            print(f"Error visiting news page: {e}")
            print("Skipping news page update")
        
        print("\n[+] Multi-page update operations completed!")
        return True
        
    except Exception as e:
        print(f"\n[X] Error during multi-page update process: {e}")
        traceback.print_exc()
        return False

def process_site(driver, site_url, site_label=None):
    """Process a single site's login and update operations"""
    try:
        label_info = f" [{site_label}]" if site_label else ""
        print(f"\n===== Processing site{label_info}: {site_url} =====")
        
        # Extract base URL from URL
        base_url = '/'.join(site_url.split('/')[:3])  # Get http(s)://domain.com part
        
        print("Navigating to website...")
        try:
            driver.get(site_url)
        except Exception as e:
            print(f"Error navigating to site: {e}")
            take_screenshot(driver, "navigation_error")
            # If navigation error, try refreshing
            try:
                print("Trying to refresh the page...")
                driver.refresh()
                time.sleep(2)
            except:
                pass
        
        # Add random delay to avoid rate limiting
        rand_delay = random.uniform(1, 3)
        time.sleep(rand_delay)
        
        # Login with retries
        login_success = False
        for login_attempt in range(LOGIN_RETRY_COUNT):
            # Check if login needed (if username input exists)
            login_fields = driver.find_elements(By.CSS_SELECTOR, "input[placeholder='User Name']")
            if not login_fields or not any(field.is_displayed() for field in login_fields):
                print("Already logged in, no need to login again")
                login_success = True
                break
                
            if login_attempt > 0:
                print(f"\n----- Login Retry Attempt {login_attempt+1}/{LOGIN_RETRY_COUNT} -----")
                # Refresh page before retry
                try:
                    print("Refreshing page before retry...")
                    driver.refresh()
                    time.sleep(3)
                except:
                    pass
            
            print("Login page detected, performing login...")
            try:
                # Wait a bit longer for login page to be fully loaded
                time.sleep(3)
                
                username_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='User Name']"))
                )
                
                print("Entering username...")
                username_field.clear()  # Clear field first
                username_field.send_keys("lixiaohui@qq.com")
                
                print("Entering password...")
                password_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Password']")
                password_field.clear()  # Clear field first
                password_field.send_keys("123456")
                
                print("Clicking login button...")
                login_button_clicked = False
                
                # Try clicking login button with standard method first
                login_success = wait_and_click(driver, "//button[contains(., 'login')]", By.XPATH, 10, "login button")
                if not login_success:
                    # Try other ways to find submit button
                    print("Trying other ways to find login button...")
                    login_buttons = driver.find_elements(By.TAG_NAME, "button")
                    for button in login_buttons:
                        if button.is_displayed() and button.is_enabled():
                            try:
                                driver.execute_script("arguments[0].click();", button)
                                print("Clicked possible login button using JavaScript")
                                login_button_clicked = True
                                break
                            except:
                                try:
                                    button.click()
                                    print("Clicked possible login button")
                                    login_button_clicked = True
                                    break
                                except:
                                    continue
                else:
                    login_button_clicked = True
                
                if not login_button_clicked:
                    print("Could not find or click any login button")
                    continue
                
                print(f"Waiting {LOGIN_WAIT_TIME} seconds for login to complete...")
                time.sleep(LOGIN_WAIT_TIME)  # Increased wait time
                
                # Try clearing cookies and cache if this is a retry
                if login_attempt > 0:
                    print("Clearing cookies for this domain...")
                    driver.delete_all_cookies()
                    time.sleep(2)
                
                # Check if still on login page
                login_fields_after = driver.find_elements(By.CSS_SELECTOR, "input[placeholder='User Name']")
                if login_fields_after and any(field.is_displayed() for field in login_fields_after):
                    print("Login appears to have failed, still on login page")
                    
                    # Check for any error messages
                    error_messages = driver.find_elements(By.CSS_SELECTOR, ".el-message--error, .error-message, .alert-danger")
                    if error_messages and any(msg.is_displayed() for msg in error_messages):
                        for msg in error_messages:
                            if msg.is_displayed():
                                print(f"Error message found: {msg.text}")
                    
                    # Continue to next retry attempt
                    continue
                else:
                    print("Login successful!")
                    login_success = True
                    break
                
            except Exception as e:
                print(f"Error during login process: {e}")
                take_screenshot(driver, "login_error")
                traceback.print_exc()
                # Continue to next retry attempt
                continue
        
        # If all login attempts failed, skip this site
        if not login_success:
            print(f"\n[X] Site{label_info} login failed after {LOGIN_RETRY_COUNT} attempts, skipping this site")
            return False
        
        # Re-navigate to target page after successful login
        print("Re-navigating to target page...")
        driver.get(site_url)
        time.sleep(5)  # Wait for page to load
        
        # Check if multi-page update should be executed
        if EXECUTE_MULTI_PAGE_UPDATE:
            # Perform multi-page update operations
            multi_page_result = perform_multi_page_updates(driver, base_url)
            if not multi_page_result:
                print(f"\n[X] Site{label_info} multi-page update operations failed")
                return False
            print(f"\n[+] Site{label_info} multi-page update operations completed successfully")
            return True
            
        # If not doing multi-page update, perform single button update
        # Find and click "更新公共样式" button
        print("Looking for update button...")
        try:
            # Try multiple ways to find the update button
            update_button_found = False
            
            # Method 1: XPath
            try:
                update_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., '更新公共样式')]"))
                )
                print("Found update button (XPath)")
                update_button_found = True
            except:
                print("Update button not found via XPath")
            
            # Method 2: Find all buttons
            if not update_button_found:
                print("Trying to find all buttons...")
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    try:
                        if "更新公共样式" in button.text and button.is_displayed():
                            update_button = button
                            update_button_found = True
                            print("Found update button (by iterating buttons)")
                            break
                    except:
                        continue
            
            if not update_button_found:
                print("Update button not found, trying to screenshot current page...")
                take_screenshot(driver, "no_update_button")
                return False
            
            print("Clicking update button...")
            try:
                driver.execute_script("arguments[0].click();", update_button)
                print("Clicked update button using JavaScript")
            except:
                try:
                    update_button.click()
                    print("Clicked update button using regular method")
                except Exception as click_error:
                    print(f"Failed to click update button: {click_error}")
                    take_screenshot(driver, "update_button_click_error")
                    return False
            
            # Handle confirmation dialog
            print("Waiting for confirmation dialog...")
            time.sleep(2)
            take_screenshot(driver, "after_update_click")
            
            # Handle confirmation dialog
            confirmation_clicked = handle_confirmation_dialog(driver)
            
            # Check deployment status
            if confirmation_clicked:
                print("Confirmation button clicked, checking deployment status...")
                deployment_result = check_deployment_status(driver, site_url)
                return deployment_result
            else:
                print("\n===================================")
                print(f"[!] Site{label_info} unable to click confirmation button, deployment may not have started.")
                print("===================================\n")
                take_screenshot(driver, "no_confirmation_button")
                return False
                
        except Exception as e:
            print(f"\n[X] Site{label_info} update process error: {e}")
            take_screenshot(driver, "update_process_error")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"\n[X] Site{label_info} processing error: {e}")
        take_screenshot(driver, "process_site_error")
        traceback.print_exc()
        return False
    
    return None  # Default return unknown status

def load_sites_from_file(file_path, include_sites=None, exclude_sites=None):
    """Load site URLs from file
    
    Args:
        file_path: Path to the file
        include_sites: List of site identifiers to include, e.g. ['tw', 'en']
        exclude_sites: List of site identifiers to exclude, e.g. ['en']
        
    Returns:
        dict: Dictionary with site identifiers and URLs, e.g. {'tw': 'http://...', 'en': 'http://...'}
    """
    try:
        if not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            return None
            
        # Determine how to load based on file extension
        ext = os.path.splitext(file_path)[1].lower()
        sites_dict = {}
        
        if ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Handle new format: urls is a dictionary
                if isinstance(data, dict) and 'urls' in data and isinstance(data['urls'], dict):
                    sites_dict = data['urls']
                    print(f"Loaded {len(sites_dict)} sites from JSON file")
                
                # Handle old format: urls is a list
                elif isinstance(data, dict) and 'urls' in data and isinstance(data['urls'], list):
                    urls_list = data['urls']
                    # Use index as key
                    for i, url in enumerate(urls_list):
                        sites_dict[f"site{i+1}"] = url
                    print(f"Loaded {len(sites_dict)} sites from JSON file (converted old format)")
                
                # Handle direct list
                elif isinstance(data, list):
                    # Use index as key
                    for i, url in enumerate(data):
                        sites_dict[f"site{i+1}"] = url
                    print(f"Loaded {len(sites_dict)} sites from JSON file (list format)")
                
                else:
                    print("Invalid JSON format, should be URL dictionary, URL list, or object with 'urls' key")
                    return None
                
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                # Remove empty lines and spaces, use line number as key
                lines = [line.strip() for line in f if line.strip()]
                for i, url in enumerate(lines):
                    sites_dict[f"site{i+1}"] = url
                print(f"Loaded {len(sites_dict)} sites from text file")
        else:
            print(f"Unsupported file type: {ext}")
            return None
            
        # Apply include and exclude filters
        filtered_dict = {}
        
        if include_sites:
            # Only include specified sites
            include_list = include_sites.split(',')
            print(f"Only including these sites: {include_list}")
            for site_id in include_list:
                if site_id in sites_dict:
                    filtered_dict[site_id] = sites_dict[site_id]
                else:
                    print(f"Warning: Specified include site '{site_id}' does not exist")
        
        elif exclude_sites:
            # Exclude specified sites
            exclude_list = exclude_sites.split(',')
            print(f"Excluding these sites: {exclude_list}")
            for site_id, url in sites_dict.items():
                if site_id not in exclude_list:
                    filtered_dict[site_id] = url
        
        else:
            # No filtering, use all sites
            filtered_dict = sites_dict
        
        print(f"Retained {len(filtered_dict)} sites after filtering")
        
        return filtered_dict
        
    except Exception as e:
        print(f"Error loading sites file: {e}")
        traceback.print_exc()
        return None

def automate_vidnoz(sites_dict=None):
    """Main function to process multiple sites in batch"""
    if sites_dict is None or not sites_dict:
        print("No valid site list provided")
        return {}
    
    # Display sites to process
    print(f"Preparing to process {len(sites_dict)} sites:")
    for i, (site_id, url) in enumerate(sites_dict.items(), 1):
        print(f"{i}. [{site_id}] {url}")
    print("\n")
    
    # Display multi-page update setting status
    if EXECUTE_MULTI_PAGE_UPDATE:
        print("[!] Multi-page update feature is enabled, will execute multi-page button click sequence")
    else:
        print("[i] Multi-page update feature is disabled, only performing regular public style update")
    
    # Display timing configuration
    print(f"[i] Login wait time: {LOGIN_WAIT_TIME} seconds")
    print(f"[i] Site interval time: {SITE_INTERVAL_TIME} seconds")
    print(f"[i] Login retry attempts: {LOGIN_RETRY_COUNT}")
    print(f"[i] Deployment wait time: {DEPLOYMENT_WAIT_TIME} seconds")
    
    # Chrome options setup
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Add headless mode to run Chrome without opening a window
    chrome_options.add_argument("--headless")
    # Add ignore SSL certificate error options
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    # Add disable infobars option
    chrome_options.add_argument("--disable-infobars")
    # Add disable extensions option
    chrome_options.add_argument("--disable-extensions")
    # Set window size to ensure elements are visible (important in headless mode)
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Add experimental options
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Add specific site processing
    results = {}
    
    # Process each site with a fresh browser instance to avoid session conflicts
    for i, (site_id, site_url) in enumerate(sites_dict.items(), 1):
        print(f"\n[{i}/{len(sites_dict)}] Processing site [{site_id}]: {site_url}")
        
        # Create a new browser instance for each site
        print(f"Starting new Chrome instance for site [{site_id}]...")
        site_driver = webdriver.Chrome(options=chrome_options)
        site_driver.set_window_size(1920, 1080)
        
        try:
            # Process this individual site
            result = process_site(site_driver, site_url, site_id)
            results[site_id] = {
                'url': site_url,
                'result': result
            }
        except Exception as e:
            print(f"\n[X] Error processing site [{site_id}]: {e}")
            traceback.print_exc()
            results[site_id] = {
                'url': site_url,
                'result': False
            }
        finally:
            # Close this browser instance
            print(f"Closing browser for site [{site_id}]...")
            try:
                site_driver.quit()
            except:
                pass
            
            # Pause between sites
            if i < len(sites_dict):
                print(f"Waiting {SITE_INTERVAL_TIME} seconds before next site...")
                time.sleep(SITE_INTERVAL_TIME)
    
    # Display summary results
    print("\n===== Batch Processing Results Summary =====")
    successful = sum(1 for site in results.values() if site['result'] is True)
    failed = sum(1 for site in results.values() if site['result'] is False)
    unknown = sum(1 for site in results.values() if site['result'] is None)
    
    print(f"Total sites: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Unknown status: {unknown}")
    
    print("\nDetailed results:")
    for site_id, site_info in results.items():
        status = "[+] Success" if site_info['result'] is True else "[X] Failed" if site_info['result'] is False else "[!] Unknown"
        print(f"{status}: [{site_id}] {site_info['url']}")
    
    print("\nProgram execution completed.")
    
    return results

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Vidnoz Site Automation Tool')
    parser.add_argument('file', nargs='?', help='Site list file path (.json or .txt)')
    parser.add_argument('--include', help='Only include specified sites, comma separated, e.g. tw,en')
    parser.add_argument('--exclude', help='Exclude specified sites, comma separated, e.g. en')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    if args.file:
        print(f"Loading site list from file: {args.file}")
        
        if args.include and args.exclude:
            print("Error: --include and --exclude options cannot be used together")
            sys.exit(1)
        
        sites = load_sites_from_file(
            args.file,
            include_sites=args.include,
            exclude_sites=args.exclude
        )
        
        if sites:
            automate_vidnoz(sites)
        else:
            print("Unable to load sites from file or no sites after filtering")
    else:
        print("No site list file provided, please specify a .json or .txt file")
        sys.exit(1) 
