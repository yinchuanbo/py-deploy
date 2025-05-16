# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import random
import traceback
import argparse
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 配置变量
DEFAULT_SITES = []
EXECUTE_MULTI_PAGE_UPDATE = False
LOGIN_WAIT_TIME = 15  # 等待登录完成的秒数
SITE_INTERVAL_TIME = 20  # 站点之间等待的秒数
LOGIN_RETRY_COUNT = 3  # 最大登录重试次数
DEPLOYMENT_WAIT_TIME = 45  # 等待部署状态的秒数

# 自动化功能部分
def take_screenshot(driver, name):
    """空函数，不进行截图"""
    return None

def wait_and_click(driver, selector, by=By.CSS_SELECTOR, timeout=10, description="element"):
    """等待元素出现并点击，带重试和详细日志"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )
        print(f"找到 {description}，尝试点击...")
        
        try:
            # 尝试使用JavaScript点击
            driver.execute_script("arguments[0].click();", element)
            print(f"成功使用JavaScript点击 {description}")
            return True
        except Exception as js_error:
            print(f"JavaScript点击失败: {js_error}")
            try:
                # 尝试常规点击
                element.click()
                print(f"成功使用常规方式点击 {description}")
                return True
            except Exception as click_error:
                print(f"常规点击失败: {click_error}")
                return False
    except TimeoutException:
        print(f"等待 {description} 超时")
        return False
    except Exception as e:
        print(f"等待/点击 {description} 错误: {e}")
        return False

def handle_confirmation_dialog(driver):
    """处理确认对话框，点击'确认'按钮"""
    confirmation_clicked = False
    
    # 尝试三次
    for attempt in range(3):
        if confirmation_clicked:
            break
            
        print(f"尝试查找并点击确认按钮 (尝试 {attempt+1}/3)...")
        
        try:
            # 获取页面上所有对话框的HTML用于调试
            page_html = driver.page_source
            dialog_html = ""
            
            dialogs = driver.find_elements(By.CSS_SELECTOR, ".el-message-box, .el-dialog, .modal, .dialog, [role='dialog']")
            print(f"找到 {len(dialogs)} 个可能的对话框")
            
            for i, dialog in enumerate(dialogs):
                try:
                    dialog_html += f"\n对话框 {i+1} HTML: {dialog.get_attribute('outerHTML')}"
                    
                    # 检查对话框是否可见
                    if not dialog.is_displayed():
                        print(f"对话框 {i+1} 不可见，跳过")
                        continue
                        
                    print(f"分析对话框 {i+1}, 文本: {dialog.text}")
                    
                    # 如果对话框包含"确认更新"文本
                    if "确认更新" in dialog.text or "确认" in dialog.text:
                        print(f"对话框 {i+1} 包含确认文本")
                        
                        # 查找所有按钮
                        buttons = dialog.find_elements(By.TAG_NAME, "button")
                        print(f"在对话框中找到 {len(buttons)} 个按钮")
                        
                        # 遍历所有按钮
                        for j, button in enumerate(buttons):
                            try:
                                button_text = button.text.strip().lower()
                                print(f"按钮 {j+1} 文本: '{button_text}'")
                                
                                if any(text in button_text for text in ['sure', 'yes', 'ok', '确认', 'confirm']):
                                    print(f"找到确认按钮: '{button_text}'")
                                    
                                    try:
                                        # 使用JavaScript点击
                                        driver.execute_script("arguments[0].click();", button)
                                        print("使用JavaScript点击确认按钮")
                                        confirmation_clicked = True
                                        time.sleep(1)
                                        break
                                    except Exception as js_error:
                                        print(f"JavaScript点击失败: {js_error}")
                                        try:
                                            # 尝试常规点击
                                            button.click()
                                            print("使用常规方式点击确认按钮")
                                            confirmation_clicked = True
                                            time.sleep(1)
                                            break
                                        except Exception as click_error:
                                            print(f"确认按钮的常规点击失败: {click_error}")
                            except Exception as button_error:
                                print(f"处理按钮 {j+1} 错误: {button_error}")
                        
                        # 如果点击成功，跳出对话框循环
                        if confirmation_clicked:
                            break
                except Exception as dialog_error:
                    print(f"处理对话框 {i+1} 错误: {dialog_error}")
            
            # 如果通过对话框没有找到按钮，尝试直接搜索
            if not confirmation_clicked:
                print("通过对话框未找到确认按钮，尝试直接搜索...")
                
                # 尝试多种选择器
                selectors = [
                    "//button[contains(., 'Sure')]",
                    "//button[contains(., 'sure')]",
                    "//button[contains(., '确认')]",
                    "//button[contains(., 'Yes')]",
                    "//button[contains(., 'OK')]",
                    "//button[contains(., 'Confirm')]",
                    ".el-button--primary",  # Element UI 主要按钮
                    ".btn-primary",          # Bootstrap 主要按钮
                    ".confirm-btn"           # 常见确认按钮类
                ]
                
                for selector in selectors:
                    try:
                        selector_type = By.XPATH if selector.startswith("//") else By.CSS_SELECTOR
                        buttons = driver.find_elements(selector_type, selector)
                        
                        print(f"选择器 '{selector}' 找到 {len(buttons)} 个按钮")
                        
                        for j, button in enumerate(buttons):
                            if button.is_displayed() and button.is_enabled():
                                try:
                                    print(f"尝试点击按钮: {button.text}")
                                    driver.execute_script("arguments[0].click();", button)
                                    print(f"使用JavaScript点击按钮")
                                    confirmation_clicked = True
                                    time.sleep(1)
                                    break
                                except Exception as js_error:
                                    print(f"JavaScript点击失败: {js_error}")
                                    try:
                                        button.click()
                                        print(f"使用常规方式点击按钮")
                                        confirmation_clicked = True
                                        time.sleep(1)
                                        break
                                    except Exception as click_error:
                                        print(f"常规点击失败: {click_error}")
                        
                        if confirmation_clicked:
                            break
                    except Exception as selector_error:
                        print(f"使用选择器 '{selector}' 时出错: {selector_error}")
            
            # 保存当前尝试的调试信息
            if not confirmation_clicked:
                print("当前尝试未找到确认按钮")
                print(f"页面对话框 HTML: {dialog_html}")
        
        except Exception as attempt_error:
            print(f"在尝试 {attempt+1} 中查找确认按钮时出错: {attempt_error}")
            traceback.print_exc()
        
        # 如果未点击且还有更多尝试，等待后再试
        if not confirmation_clicked and attempt < 2:
            print(f"等待2秒后进行下一次尝试...")
            time.sleep(2)
    
    return confirmation_clicked

def check_deployment_status(driver, site_url):
    """检查部署状态，返回True（成功），False（失败）或None（未知）"""
    # 更长时间等待部署状态指示器
    max_wait_time = DEPLOYMENT_WAIT_TIME  # 从30秒增加到45秒
    start_time = time.time()
    deployment_status_found = False
    
    while time.time() - start_time < max_wait_time and not deployment_status_found:
        try:
            # 检查部署失败（.blog-login元素）
            login_elements = driver.find_elements(By.CSS_SELECTOR, ".blog-login")
            if login_elements and any(element.is_displayed() for element in login_elements):
                print("\n===================================")
                print(f"[X] 站点 {site_url} 部署失败！系统可能已登出。")
                print("===================================\n")
                deployment_status_found = True
                return False
            
            # 检查部署成功（.el-message--success元素）
            success_elements = driver.find_elements(By.CSS_SELECTOR, ".el-message--success")
            if success_elements and any(element.is_displayed() for element in success_elements):
                print("\n===================================")
                print(f"[+] 站点 {site_url} 部署成功！样式已更新。")
                print("===================================\n")
                deployment_status_found = True
                return True
            
            # 扩展检查：寻找可能表示成功的元素
            success_indicators = driver.find_elements(By.CSS_SELECTOR, ".success, .alert-success, .text-success")
            if success_indicators and any(element.is_displayed() for element in success_indicators):
                print("\n===================================")
                print(f"[+] 站点 {site_url} 似乎已成功部署！找到成功指示器。")
                print("===================================\n")
                deployment_status_found = True
                return True
                
            # 等待一下再次检查
            time.sleep(1)
            print(f"等待部署状态... 已等待 {int(time.time() - start_time)} 秒", end="\r")
        except Exception as e:
            print(f"检查部署状态时出错: {e}")
            time.sleep(1)
    
    if not deployment_status_found:
        print("\n===================================")
        print(f"[!] 站点 {site_url} 部署状态未知！超时，请手动检查。")
        print("===================================\n")
        return None
    
    return None

def click_button_with_confirmation(driver, button_text, site_url):
    """点击指定文本的按钮，处理确认对话框，检查部署状态"""
    try:
        print(f"\n----- 尝试点击按钮: '{button_text}' -----")
        
        # 尝试查找按钮
        button_found = False
        
        # 方法1：通过包含文本的XPath查找按钮
        try:
            button_xpath = f"//button[contains(., '{button_text}')]"
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, button_xpath))
            )
            button_found = True
            print(f"找到按钮: '{button_text}' (XPath)")
        except:
            print(f"通过XPath未找到按钮: '{button_text}'")
        
        # 方法2：遍历所有按钮
        if not button_found:
            print("尝试遍历所有按钮...")
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                try:
                    if button_text in btn.text and btn.is_displayed():
                        button = btn
                        button_found = True
                        print(f"找到按钮: '{button_text}' (遍历)")
                        break
                except:
                    continue
        
        if not button_found:
            print(f"未找到按钮: '{button_text}'")
            return False
        
        # 点击按钮
        try:
            driver.execute_script("arguments[0].click();", button)
            print(f"使用JavaScript点击按钮: '{button_text}'")
        except:
            try:
                button.click()
                print(f"使用常规方式点击按钮: '{button_text}'")
            except Exception as click_error:
                print(f"无法点击按钮 '{button_text}': {click_error}")
                return False
        
        # 等待确认对话框出现
        print("等待确认对话框...")
        time.sleep(2)
        
        # 处理确认对话框
        confirmation_clicked = handle_confirmation_dialog(driver)
        
        if not confirmation_clicked:
            print(f"\n===================================")
            print(f"[!] 无法点击确认按钮，'{button_text}' 可能未执行。")
            print("===================================\n")
            return False
        
        # 检查部署状态
        print(f"检查 '{button_text}' 部署状态...")
        deployment_result = check_deployment_status(driver, site_url)
        
        if deployment_result is False:
            # 部署失败，返回失败
            return False
        
        # 部署成功或状态未知，继续
        return True
        
    except Exception as e:
        print(f"按钮点击过程 '{button_text}' 出错: {e}")
        traceback.print_exc()
        return False

def perform_multi_page_updates(driver, base_url):
    """执行多页面按钮点击更新操作"""
    if not EXECUTE_MULTI_PAGE_UPDATE:
        print("\n多页面更新功能已禁用。要启用，请将 EXECUTE_MULTI_PAGE_UPDATE 设置为 True\n")
        return True
    
    print("\n===== 开始多页面更新操作 =====\n")
    
    try:
        # 1. 文章列表页面 - aritcle-list
        article_page = f"{base_url}/frontend/page/aritcle-list"
        print(f"\n[1/3] 访问文章列表页面: {article_page}")
        driver.get(article_page)
        time.sleep(3)
        
        # 按顺序点击按钮
        article_buttons = ["更新公共样式", "更新blog全部列表", "更新blog全部详情"]
        for btn_text in article_buttons:
            if not click_button_with_confirmation(driver, btn_text, article_page):
                print(f"\n[X] 无法在文章页面上点击 '{btn_text}'，中止操作")
                return False
            time.sleep(2)  # 按钮之间等待
        
        # 2. FAQ列表页面 - faq-list
        faq_page = f"{base_url}/frontend/page/faq-list"
        print(f"\n[2/3] 访问FAQ列表页面: {faq_page}")
        driver.get(faq_page)
        time.sleep(3)
        
        # 按顺序点击按钮
        faq_buttons = ["更新公共样式", "更新faq全部列表", "更新faq全部详情"]
        for btn_text in faq_buttons:
            if not click_button_with_confirmation(driver, btn_text, faq_page):
                print(f"\n[X] 无法在FAQ页面上点击 '{btn_text}'，中止操作")
                return False
            time.sleep(2)  # 按钮之间等待
        
        # 3. 新闻页面 - pressroom-list（可能不存在）
        pressroom_page = f"{base_url}/frontend/page/pressroom-list"
        print(f"\n[3/3] 尝试访问新闻页面: {pressroom_page}")
        
        # 检查页面是否存在
        try:
            driver.get(pressroom_page)
            time.sleep(3)
            
            # 检查页面是否加载了预期内容
            try:
                # 尝试找到至少一个按钮以确认页面已正确加载
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(., '更新公共样式')]"))
                )
                print("新闻页面存在，继续执行")
                
                # 按顺序点击按钮
                pressroom_buttons = ["更新公共样式", "更新pressroom全部列表", "更新pressroom全部详情"]
                for btn_text in pressroom_buttons:
                    if not click_button_with_confirmation(driver, btn_text, pressroom_page):
                        print(f"\n[X] 无法在新闻页面上点击 '{btn_text}'，中止操作")
                        return False
                    time.sleep(2)  # 按钮之间等待
                
            except (TimeoutException, NoSuchElementException):
                print("新闻页面不存在或找不到预期按钮，跳过此页面")
        
        except Exception as e:
            print(f"访问新闻页面时出错: {e}")
            print("跳过新闻页面更新")
        
        print("\n[+] 多页面更新操作已完成！")
        return True
        
    except Exception as e:
        print(f"\n[X] 多页面更新过程中出错: {e}")
        traceback.print_exc()
        return False 

def process_site(driver, site_url, site_label=None):
    """处理单个站点的登录和更新操作"""
    try:
        label_info = f" [{site_label}]" if site_label else ""
        print(f"\n===== 处理站点{label_info}: {site_url} =====")
        
        # 从URL中提取基本URL
        base_url = '/'.join(site_url.split('/')[:3])  # 获取http(s)://domain.com部分
        
        print("导航到网站...")
        try:
            driver.get(site_url)
        except Exception as e:
            print(f"导航到站点时出错: {e}")
            take_screenshot(driver, "navigation_error")
            # 如果导航错误，尝试刷新
            try:
                print("尝试刷新页面...")
                driver.refresh()
                time.sleep(2)
            except:
                pass
        
        # 添加随机延迟以避免速率限制
        rand_delay = random.uniform(1, 3)
        time.sleep(rand_delay)
        
        # 登录重试
        login_success = False
        for login_attempt in range(LOGIN_RETRY_COUNT):
            # 检查是否需要登录（如果用户名输入存在）
            login_fields = driver.find_elements(By.CSS_SELECTOR, "input[placeholder='User Name']")
            if not login_fields or not any(field.is_displayed() for field in login_fields):
                print("已经登录，无需再次登录")
                login_success = True
                break
                
            if login_attempt > 0:
                print(f"\n----- 登录重试尝试 {login_attempt+1}/{LOGIN_RETRY_COUNT} -----")
                # 重试前刷新页面
                try:
                    print("重试前刷新页面...")
                    driver.refresh()
                    time.sleep(3)
                except:
                    pass
            
            print("检测到登录页面，正在执行登录...")
            try:
                # 等待登录页面完全加载
                time.sleep(3)
                
                username_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='User Name']"))
                )
                
                print("输入用户名...")
                username_field.clear()  # 先清除字段
                username_field.send_keys("lixiaohui@qq.com")
                
                print("输入密码...")
                password_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Password']")
                password_field.clear()  # 先清除字段
                password_field.send_keys("123456")
                
                print("点击登录按钮...")
                login_button_clicked = False
                
                # 首先尝试使用标准方法点击登录按钮
                login_success = wait_and_click(driver, "//button[contains(., 'login')]", By.XPATH, 10, "登录按钮")
                if not login_success:
                    # 尝试其他方式查找提交按钮
                    print("尝试其他方式查找登录按钮...")
                    login_buttons = driver.find_elements(By.TAG_NAME, "button")
                    for button in login_buttons:
                        if button.is_displayed() and button.is_enabled():
                            try:
                                driver.execute_script("arguments[0].click();", button)
                                print("使用JavaScript点击可能的登录按钮")
                                login_button_clicked = True
                                break
                            except:
                                try:
                                    button.click()
                                    print("点击可能的登录按钮")
                                    login_button_clicked = True
                                    break
                                except:
                                    continue
                else:
                    login_button_clicked = True
                
                if not login_button_clicked:
                    print("无法找到或点击任何登录按钮")
                    continue
                
                print(f"等待 {LOGIN_WAIT_TIME} 秒让登录完成...")
                time.sleep(LOGIN_WAIT_TIME)  # 增加等待时间
                
                # 如果这是重试，尝试清除cookie和缓存
                if login_attempt > 0:
                    print("为此域清除cookie...")
                    driver.delete_all_cookies()
                    time.sleep(2)
                
                # 检查是否仍在登录页面
                login_fields_after = driver.find_elements(By.CSS_SELECTOR, "input[placeholder='User Name']")
                if login_fields_after and any(field.is_displayed() for field in login_fields_after):
                    print("登录似乎失败，仍在登录页面")
                    
                    # 检查任何错误消息
                    error_messages = driver.find_elements(By.CSS_SELECTOR, ".el-message--error, .error-message, .alert-danger")
                    if error_messages and any(msg.is_displayed() for msg in error_messages):
                        for msg in error_messages:
                            if msg.is_displayed():
                                print(f"发现错误消息: {msg.text}")
                    
                    # 继续下一次重试尝试
                    continue
                else:
                    print("登录成功！")
                    login_success = True
                    break
                
            except Exception as e:
                print(f"登录过程中出错: {e}")
                take_screenshot(driver, "login_error")
                traceback.print_exc()
                # 继续下一次重试尝试
                continue
        
        # 如果所有登录尝试失败，跳过此站点
        if not login_success:
            print(f"\n[X] 站点{label_info}登录失败，经过 {LOGIN_RETRY_COUNT} 次尝试，跳过此站点")
            return False
        
        # 登录成功后重新导航到目标页面
        print("重新导航到目标页面...")
        driver.get(site_url)
        time.sleep(5)  # 等待页面加载
        
        # 检查是否应执行多页面更新
        if EXECUTE_MULTI_PAGE_UPDATE:
            # 执行多页面更新操作
            multi_page_result = perform_multi_page_updates(driver, base_url)
            if not multi_page_result:
                print(f"\n[X] 站点{label_info}多页面更新操作失败")
                return False
            print(f"\n[+] 站点{label_info}多页面更新操作成功完成")
            return True
            
        # 如果不执行多页面更新，执行单按钮更新
        # 查找并点击"更新公共样式"按钮
        print("寻找更新按钮...")
        try:
            # 尝试多种方法找到更新按钮
            update_button_found = False
            
            # 方法1：XPath
            try:
                update_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., '更新公共样式')]"))
                )
                print("找到更新按钮 (XPath)")
                update_button_found = True
            except:
                print("通过XPath未找到更新按钮")
            
            # 方法2：查找所有按钮
            if not update_button_found:
                print("尝试查找所有按钮...")
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    try:
                        if "更新公共样式" in button.text and button.is_displayed():
                            update_button = button
                            update_button_found = True
                            print("找到更新按钮（通过遍历按钮）")
                            break
                    except:
                        continue
            
            if not update_button_found:
                print("未找到更新按钮，尝试截取当前页面...")
                take_screenshot(driver, "no_update_button")
                return False
            
            print("点击更新按钮...")
            try:
                driver.execute_script("arguments[0].click();", update_button)
                print("使用JavaScript点击更新按钮")
            except:
                try:
                    update_button.click()
                    print("使用常规方法点击更新按钮")
                except Exception as click_error:
                    print(f"无法点击更新按钮: {click_error}")
                    take_screenshot(driver, "update_button_click_error")
                    return False
            
            # 处理确认对话框
            print("等待确认对话框...")
            time.sleep(2)
            take_screenshot(driver, "after_update_click")
            
            # 处理确认对话框
            confirmation_clicked = handle_confirmation_dialog(driver)
            
            # 检查部署状态
            if confirmation_clicked:
                print("已点击确认按钮，检查部署状态...")
                deployment_result = check_deployment_status(driver, site_url)
                return deployment_result
            else:
                print("\n===================================")
                print(f"[!] 站点{label_info}无法点击确认按钮，部署可能未开始。")
                print("===================================\n")
                take_screenshot(driver, "no_confirmation_button")
                return False
                
        except Exception as e:
            print(f"\n[X] 站点{label_info}更新过程错误: {e}")
            take_screenshot(driver, "update_process_error")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"\n[X] 站点{label_info}处理错误: {e}")
        take_screenshot(driver, "process_site_error")
        traceback.print_exc()
        return False
    
    return None  # 默认返回未知状态

def load_sites_from_file(file_path, include_sites=None, exclude_sites=None):
    """从文件加载站点URL
    
    Args:
        file_path: 文件路径
        include_sites: 要包含的站点标识符列表，例如['tw', 'en']
        exclude_sites: 要排除的站点标识符列表，例如['en']
        
    Returns:
        dict: 具有站点标识符和URL的字典，例如{'tw': 'http://...', 'en': 'http://...'}
    """
    try:
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return None
            
        # 根据文件扩展名确定如何加载
        ext = os.path.splitext(file_path)[1].lower()
        sites_dict = {}
        
        if ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 处理新格式：urls是一个字典
                if isinstance(data, dict) and 'urls' in data and isinstance(data['urls'], dict):
                    sites_dict = data['urls']
                    print(f"从JSON文件加载了 {len(sites_dict)} 个站点")
                
                # 处理旧格式：urls是一个列表
                elif isinstance(data, dict) and 'urls' in data and isinstance(data['urls'], list):
                    urls_list = data['urls']
                    # 使用索引作为键
                    for i, url in enumerate(urls_list):
                        sites_dict[f"site{i+1}"] = url
                    print(f"从JSON文件加载了 {len(sites_dict)} 个站点（转换了旧格式）")
                
                # 处理直接列表
                elif isinstance(data, list):
                    # 使用索引作为键
                    for i, url in enumerate(data):
                        sites_dict[f"site{i+1}"] = url
                    print(f"从JSON文件加载了 {len(sites_dict)} 个站点（列表格式）")
                
                else:
                    print("无效的JSON格式，应该是URL字典、URL列表或带有'urls'键的对象")
                    return None
                
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                # 删除空行和空格，使用行号作为键
                lines = [line.strip() for line in f if line.strip()]
                for i, url in enumerate(lines):
                    sites_dict[f"site{i+1}"] = url
                print(f"从文本文件加载了 {len(sites_dict)} 个站点")
        else:
            print(f"不支持的文件类型: {ext}")
            return None
            
        # 应用包含和排除过滤器
        filtered_dict = {}
        
        if include_sites:
            # 仅包括指定站点
            include_list = include_sites.split(',')
            print(f"仅包含这些站点: {include_list}")
            for site_id in include_list:
                if site_id in sites_dict:
                    filtered_dict[site_id] = sites_dict[site_id]
                else:
                    print(f"警告: 指定的包含站点 '{site_id}' 不存在")
        
        elif exclude_sites:
            # 排除指定站点
            exclude_list = exclude_sites.split(',')
            print(f"排除这些站点: {exclude_list}")
            for site_id, url in sites_dict.items():
                if site_id not in exclude_list:
                    filtered_dict[site_id] = url
        
        else:
            # 无过滤，使用所有站点
            filtered_dict = sites_dict
        
        print(f"过滤后保留了 {len(filtered_dict)} 个站点")
        
        return filtered_dict
        
    except Exception as e:
        print(f"加载站点文件时出错: {e}")
        traceback.print_exc()
        return None 

def automate_vidnoz(sites_dict=None):
    """处理多个站点的主函数"""
    if sites_dict is None or not sites_dict:
        print("未提供有效的站点列表")
        return {}
    
    # 显示要处理的站点
    print(f"准备处理 {len(sites_dict)} 个站点:")
    for i, (site_id, url) in enumerate(sites_dict.items()):
        print(f"{i}. [{site_id}] {url}")
    print("\n")
    
    # 显示多页面更新设置状态
    if EXECUTE_MULTI_PAGE_UPDATE:
        print("[!] 多页面更新功能已启用，将执行多页面按钮点击序列")
    else:
        print("[i] 多页面更新功能已禁用，仅执行常规公共样式更新")
    
    # 显示计时配置
    print(f"[i] 登录等待时间: {LOGIN_WAIT_TIME} 秒")
    print(f"[i] 站点间隔时间: {SITE_INTERVAL_TIME} 秒")
    print(f"[i] 登录重试次数: {LOGIN_RETRY_COUNT}")
    print(f"[i] 部署等待时间: {DEPLOYMENT_WAIT_TIME} 秒")
    
    # Chrome选项设置
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # 添加无头模式以在不打开窗口的情况下运行Chrome
    chrome_options.add_argument("--headless")
    # 添加忽略SSL证书错误选项
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    # 添加禁用信息栏选项
    chrome_options.add_argument("--disable-infobars")
    # 添加禁用扩展选项
    chrome_options.add_argument("--disable-extensions")
    # 设置窗口大小以确保元素可见（在无头模式下很重要）
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 添加实验选项
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # 添加特定站点处理
    results = {}
    
    # 使用全新的浏览器实例处理每个站点，以避免会话冲突
    for i, (site_id, site_url) in enumerate(sites_dict.items(), 1):
        print(f"\n[{i}/{len(sites_dict)}] 处理站点 [{site_id}]: {site_url}")
        
        # 为每个站点创建新的浏览器实例
        print(f"为站点 [{site_id}] 启动新的Chrome实例...")
        site_driver = webdriver.Chrome(options=chrome_options)
        site_driver.set_window_size(1920, 1080)
        
        try:
            # 处理此单个站点
            result = process_site(site_driver, site_url, site_id)
            results[site_id] = {
                'url': site_url,
                'result': result
            }
        except Exception as e:
            print(f"\n[X] 处理站点 [{site_id}] 时出错: {e}")
            traceback.print_exc()
            results[site_id] = {
                'url': site_url,
                'result': False
            }
        finally:
            # 关闭此浏览器实例
            print(f"关闭站点 [{site_id}] 的浏览器...")
            try:
                site_driver.quit()
            except:
                pass
            
            # 站点之间暂停
            if i < len(sites_dict):
                print(f"等待 {SITE_INTERVAL_TIME} 秒后继续下一个站点...")
                time.sleep(SITE_INTERVAL_TIME)
    
    # 显示摘要结果
    print("\n===== 批处理结果摘要 =====")
    successful = sum(1 for site in results.values() if site['result'] is True)
    failed = sum(1 for site in results.values() if site['result'] is False)
    unknown = sum(1 for site in results.values() if site['result'] is None)
    
    print(f"总站点: {len(results)}")
    print(f"成功: {successful}")
    print(f"失败: {failed}")
    print(f"未知状态: {unknown}")
    
    print("\n详细结果:")
    for site_id, site_info in results.items():
        status = "[+] 成功" if site_info['result'] is True else "[X] 失败" if site_info['result'] is False else "[!] 未知"
        print(f"{status}: [{site_id}] {site_info['url']}")
    
    print("\n程序执行完成。")
    
    return results

# 重定向控制台输出到GUI
class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""
        
    def write(self, string):
        self.buffer += string
        if '\n' in self.buffer or len(self.buffer) > 80:
            self.flush()
    
    def flush(self):
        if self.buffer:
            self.text_widget.configure(state="normal")
            self.text_widget.insert(tk.END, self.buffer)
            self.text_widget.see(tk.END)
            self.text_widget.configure(state="disabled")
            self.buffer = ""

# 加载站点配置
def load_sites_config():
    """加载站点配置从sites.json文件或使用内置配置"""
    # 内置默认配置
    default_config = {
        "en": "http://manage.vidnoz.com/frontend/login",
        "jp": "http://manage-jp.vidnoz.com/frontend/login",
        "it": "http://manage-it.vidnoz.com/frontend/login",
        "fr": "http://manage-fr.vidnoz.com/frontend/login",
        "de": "http://manage-de.vidnoz.com/frontend/login",
        "ar": "http://manage-ar.vidnoz.com/frontend/login",
        "pt": "http://manage-pt.vidnoz.com/frontend/login",
        "es": "http://manage-es.vidnoz.com/frontend/login",
        "kr": "http://manage-kr.vidnoz.com/frontend/login",
        "nl": "http://manage-nl.vidnoz.com/frontend/login",
        "tr": "http://manage-tr.vidnoz.com/frontend/login",
        "tw": "http://manage-tw.vidnoz.com/frontend/login"
    }
    
    try:
        # 确定脚本位置和sites.json路径
        if getattr(sys, 'frozen', False):
            # PyInstaller创建临时文件夹，存储在_MEIPASS中
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            script_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            # 普通Python运行
            script_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = script_dir
        
        sites_path = os.path.join(script_dir, "sites.json")
        print(f"尝试从以下位置加载站点配置: {sites_path}")
        
        if not os.path.exists(sites_path):
            # 尝试在基本目录中查找
            sites_path = os.path.join(base_dir, "sites.json")
            print(f"在脚本目录中未找到sites.json，尝试: {sites_path}")
            if not os.path.exists(sites_path):
                # 尝试在当前工作目录中查找
                sites_path = os.path.join(os.getcwd(), "sites.json")
                print(f"在基本目录中未找到sites.json，尝试: {sites_path}")
                if not os.path.exists(sites_path):
                    print("未找到sites.json文件，使用内置默认配置")
                    
                    # 可选：将默认配置保存到文件中，以便用户之后编辑
                    try:
                        with open(os.path.join(script_dir, "sites.json"), 'w', encoding='utf-8') as f:
                            json.dump({"urls": default_config}, f, ensure_ascii=False, indent=4)
                            print(f"已将默认配置保存到: {os.path.join(script_dir, 'sites.json')}")
                    except Exception as save_error:
                        print(f"保存默认配置文件时出错: {save_error}")
                    
                    return default_config
        
        print(f"使用站点配置: {sites_path}")
        
        with open(sites_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'urls' in data and isinstance(data['urls'], dict):
                return data['urls']
            else:
                print("无效的站点配置格式，使用内置默认配置")
                return default_config
    except Exception as e:
        print(f"加载站点配置出错: {e}")
        print("使用内置默认配置")
        traceback.print_exc()
        return default_config

# 主应用
class VidnozApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vidnoz 自动化工具")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # 设置图标（如果有的话）
        try:
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(sys.executable)), "icon.ico")
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
        except:
            pass
        
        # 加载站点配置
        self.sites = load_sites_config()
        if not self.sites:
            messagebox.showerror("错误", "无法加载站点配置，请确保sites.json文件存在")
            root.destroy()
            return
        
        # 创建界面
        self.create_widgets()
        
        # 任务运行状态
        self.is_running = False
        self.thread = None
        
        # 定时器更新UI
        self.update_ui()
    
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 站点选择区域
        sites_frame = ttk.Frame(control_frame)
        sites_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 站点选择模式
        self.site_mode = tk.StringVar(value="all")
        ttk.Label(sites_frame, text="站点选择:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        site_mode_frame = ttk.Frame(sites_frame)
        site_mode_frame.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Radiobutton(site_mode_frame, text="所有站点", variable=self.site_mode, value="all", 
                      command=self.update_site_selection).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(site_mode_frame, text="包含特定站点", variable=self.site_mode, value="include", 
                      command=self.update_site_selection).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(site_mode_frame, text="排除特定站点", variable=self.site_mode, value="exclude", 
                      command=self.update_site_selection).pack(side=tk.LEFT, padx=5)
        
        # 站点多选框架
        self.sites_selection_frame = ttk.Frame(sites_frame)
        self.sites_selection_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # 站点复选框
        self.site_vars = {}
        self.site_checkbuttons = {}
        
        # 每行显示4个站点选项
        for i, (site_id, url) in enumerate(self.sites.items()):
            var = tk.BooleanVar(value=False)
            self.site_vars[site_id] = var
            row, col = divmod(i, 4)
            cb = ttk.Checkbutton(self.sites_selection_frame, text=f"{site_id} ({url.split('/')[2]})", 
                               variable=var, state=tk.DISABLED)
            cb.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            self.site_checkbuttons[site_id] = cb
        
        # 更新模式
        options_frame = ttk.Frame(control_frame)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(options_frame, text="更新模式:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.update_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="多页面更新（更新所有页面和样式）", 
                      variable=self.update_mode).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 控制按钮
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.start_button = ttk.Button(buttons_frame, text="开始执行", command=self.start_automation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(buttons_frame, text="停止", state=tk.DISABLED, command=self.stop_automation)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="执行日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=20, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 初始站点选择状态
        self.update_site_selection()
    
    def update_site_selection(self):
        mode = self.site_mode.get()
        
        for site_id, checkbutton in self.site_checkbuttons.items():
            if mode == "all":
                checkbutton.configure(state=tk.DISABLED)
                self.site_vars[site_id].set(False)
            else:
                checkbutton.configure(state=tk.NORMAL)
    
    def get_selected_sites(self):
        mode = self.site_mode.get()
        
        if mode == "all":
            return self.sites.copy()
        
        # 获取选中的站点
        selected = {}
        for site_id, var in self.site_vars.items():
            if var.get() and site_id in self.sites:
                selected[site_id] = self.sites[site_id]
        
        # 如果是包含模式，直接返回选中的站点
        if mode == "include":
            return selected
        
        # 如果是排除模式，返回未选中的站点
        excluded = {}
        for site_id, url in self.sites.items():
            if site_id not in selected:
                excluded[site_id] = url
        
        return excluded
    
    def start_automation(self):
        if self.is_running:
            return
        
        # 获取选中的站点
        sites_to_process = self.get_selected_sites()
        
        if not sites_to_process:
            messagebox.showwarning("警告", "没有选择任何站点，请至少选择一个站点")
            return
        
        # 设置多页面更新模式
        global EXECUTE_MULTI_PAGE_UPDATE
        EXECUTE_MULTI_PAGE_UPDATE = self.update_mode.get()
        
        # 清空日志
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
        # 禁用开始按钮
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        
        # 重定向控制台输出
        self.original_stdout = sys.stdout
        self.redirector = ConsoleRedirector(self.log_text)
        sys.stdout = self.redirector
        
        # 更新状态
        self.is_running = True
        self.status_var.set("正在执行...")
        
        # 创建新线程执行自动化任务
        self.thread = threading.Thread(target=self.run_automation, args=(sites_to_process,))
        self.thread.daemon = True
        self.thread.start()
    
    def run_automation(self, sites):
        try:
            # 执行自动化任务
            automate_vidnoz(sites)
        except Exception as e:
            print(f"\n[X] 执行过程中发生错误: {e}")
            traceback.print_exc()
        finally:
            # 恢复控制台输出
            sys.stdout = self.original_stdout
            
            # 更新UI状态
            if self.is_running:
                self.is_running = False
                # 使用after方法确保在主线程中更新UI
                self.root.after(0, self.update_after_completion)
    
    def update_after_completion(self):
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.status_var.set("执行完成")
        
        # 刷新最后的日志
        if hasattr(self, 'redirector'):
            self.redirector.flush()
    
    def stop_automation(self):
        if not self.is_running:
            return
        
        self.is_running = False
        self.status_var.set("正在停止...")
        
        # 注意：简单地将is_running设为False只能在主代码中检查时起作用
        # Selenium无法直接中断，但下一个站点不会开始
        print("\n用户请求停止处理，将在当前站点完成后退出...")
    
    def update_ui(self):
        # 定时更新UI
        if hasattr(self, 'redirector'):
            self.redirector.flush()
        
        # 每100毫秒更新一次UI
        self.root.after(100, self.update_ui)

# 主程序
def main():
    try:
        # 确保应用在PyInstaller打包后能找到正确路径
        if getattr(sys, 'frozen', False):
            # 运行打包后的应用
            os.chdir(os.path.dirname(sys.executable))
        else:
            # 运行源代码
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        root = tk.Tk()
        app = VidnozApp(root)
        root.mainloop()
    except Exception as e:
        print(f"程序错误: {e}")
        traceback.print_exc()
        
        # 如果GUI初始化失败，尝试显示错误对话框
        try:
            if 'root' in locals() and root:
                messagebox.showerror("程序错误", f"发生了一个未预期的错误：\n{e}")
            else:
                input(f"发生了一个未预期的错误：{e}\n按Enter键退出...")
        except:
            pass

if __name__ == "__main__":
    main() 