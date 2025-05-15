from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, NoSuchElementException
import time
import sys
import json
import os
import traceback
import argparse

DEFAULT_SITES = []

# 人工控制变量，决定是否执行多页面按钮点击序列
EXECUTE_MULTI_PAGE_UPDATE = False

def take_screenshot(driver, name):
    """空函数，不执行截图操作"""
    # 已禁用截图功能
    return None

def wait_and_click(driver, selector, by=By.CSS_SELECTOR, timeout=10, description="元素"):
    """等待元素出现并点击，带有重试和详细日志"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )
        print(f"找到{description}，尝试点击...")
        
        try:
            # 尝试使用JavaScript点击
            driver.execute_script("arguments[0].click();", element)
            print(f"使用JavaScript成功点击{description}")
            return True
        except Exception as js_error:
            print(f"JavaScript点击失败: {js_error}")
            try:
                # 尝试常规点击
                element.click()
                print(f"使用常规方法成功点击{description}")
                return True
            except Exception as click_error:
                print(f"常规点击失败: {click_error}")
                return False
    except TimeoutException:
        print(f"等待{description}超时")
        return False
    except Exception as e:
        print(f"等待/点击{description}时出错: {e}")
        return False

def handle_confirmation_dialog(driver):
    """处理确认对话框，点击Sure按钮"""
    confirmation_clicked = False
    
    # 尝试三次
    for attempt in range(3):
        if confirmation_clicked:
            break
            
        print(f"尝试找到并点击确认按钮 (尝试 {attempt+1}/3)...")
        
        try:
            # 获取页面中所有对话框的HTML，用于调试
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
                    
                    # 如果对话框包含"确认更新"字样
                    if "确认更新" in dialog.text or "确认" in dialog.text:
                        print(f"对话框 {i+1} 包含确认文本")
                        
                        # 查找所有按钮
                        buttons = dialog.find_elements(By.TAG_NAME, "button")
                        print(f"对话框中找到 {len(buttons)} 个按钮")
                        
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
                                            print("使用常规方法点击确认按钮")
                                            confirmation_clicked = True
                                            time.sleep(1)
                                            break
                                        except Exception as click_error:
                                            print(f"常规点击确认按钮失败: {click_error}")
                            except Exception as button_error:
                                print(f"处理按钮 {j+1} 时出错: {button_error}")
                        
                        # 如果点击成功，跳出对话框循环
                        if confirmation_clicked:
                            break
                except Exception as dialog_error:
                    print(f"处理对话框 {i+1} 时出错: {dialog_error}")
            
            # 如果通过对话框未找到按钮，尝试直接查找按钮
            if not confirmation_clicked:
                print("通过对话框未找到确认按钮，尝试直接查找...")
                
                # 尝试多种选择器
                selectors = [
                    "//button[contains(., 'Sure')]",
                    "//button[contains(., 'sure')]",
                    "//button[contains(., '确认')]",
                    "//button[contains(., 'Yes')]",
                    "//button[contains(., 'OK')]",
                    "//button[contains(., 'Confirm')]",
                    ".el-button--primary",  # Element UI的主要按钮
                    ".btn-primary",          # Bootstrap的主要按钮
                    ".confirm-btn"           # 常见的确认按钮类
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
                                    print(f"使用JavaScript点击了按钮")
                                    confirmation_clicked = True
                                    time.sleep(1)
                                    break
                                except Exception as js_error:
                                    print(f"JavaScript点击失败: {js_error}")
                                    try:
                                        button.click()
                                        print(f"使用常规方法点击了按钮")
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
                print(f"页面对话框HTML: {dialog_html}")
        
        except Exception as attempt_error:
            print(f"尝试 {attempt+1} 查找确认按钮时出错: {attempt_error}")
            traceback.print_exc()
        
        # 如果未点击并且还有更多尝试，等待一下再试
        if not confirmation_clicked and attempt < 2:
            print(f"等待 2 秒后进行下一次尝试...")
            time.sleep(2)
    
    return confirmation_clicked

def check_deployment_status(driver, site_url):
    """检查部署状态，返回True(成功)、False(失败)或None(未知)"""
    # 等待最多30秒，检查成功或失败指示器
    max_wait_time = 30
    start_time = time.time()
    deployment_status_found = False
    
    while time.time() - start_time < max_wait_time and not deployment_status_found:
        try:
            # 检查部署失败 (.blog-login 元素)
            login_elements = driver.find_elements(By.CSS_SELECTOR, ".blog-login")
            if login_elements and any(element.is_displayed() for element in login_elements):
                print("\n===================================")
                print(f"❌ 站点 {site_url} 部署失败！系统可能已退出登录状态。")
                print("===================================\n")
                deployment_status_found = True
                return False
            
            # 检查部署成功 (.el-message--success 元素)
            success_elements = driver.find_elements(By.CSS_SELECTOR, ".el-message--success")
            if success_elements and any(element.is_displayed() for element in success_elements):
                print("\n===================================")
                print(f"✅ 站点 {site_url} 部署成功！样式已成功更新。")
                print("===================================\n")
                deployment_status_found = True
                return True
            
            # 扩展检查：查找任何可能表示成功的元素
            success_indicators = driver.find_elements(By.CSS_SELECTOR, ".success, .alert-success, .text-success")
            if success_indicators and any(element.is_displayed() for element in success_indicators):
                print("\n===================================")
                print(f"✅ 站点 {site_url} 似乎部署成功！发现成功指示器。")
                print("===================================\n")
                deployment_status_found = True
                return True
                
            # 稍等一下再次检查
            time.sleep(1)
            print(f"等待部署状态... 已等待 {int(time.time() - start_time)} 秒", end="\r")
        except Exception as e:
            print(f"检查部署状态时出错: {e}")
            time.sleep(1)
    
    if not deployment_status_found:
        print("\n===================================")
        print(f"⚠️ 站点 {site_url} 部署状态未知！等待超时，请手动检查。")
        print("===================================\n")
        return None
    
    return None

def click_button_with_confirmation(driver, button_text, site_url):
    """点击指定文本的按钮，处理确认对话框，并检查部署状态"""
    try:
        print(f"\n----- 尝试点击按钮: '{button_text}' -----")
        
        # 尝试找到按钮
        button_found = False
        
        # 方法1：通过XPath查找包含文本的按钮
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
                print(f"使用常规方法点击按钮: '{button_text}'")
            except Exception as click_error:
                print(f"点击按钮'{button_text}'失败: {click_error}")
                return False
        
        # 等待确认对话框出现
        print("等待确认对话框...")
        time.sleep(2)
        
        # 处理确认对话框
        confirmation_clicked = handle_confirmation_dialog(driver)
        
        if not confirmation_clicked:
            print(f"\n===================================")
            print(f"⚠️ 无法点击确认按钮，'{button_text}'可能未执行。")
            print("===================================\n")
            return False
        
        # 检查部署状态
        print(f"检查'{button_text}'部署状态...")
        deployment_result = check_deployment_status(driver, site_url)
        
        if deployment_result is False:
            # 部署失败，返回失败结果
            return False
        
        # 部署成功或状态未知，继续执行
        return True
        
    except Exception as e:
        print(f"点击按钮'{button_text}'过程中出错: {e}")
        traceback.print_exc()
        return False

def perform_multi_page_updates(driver, base_url):
    """执行多页面的按钮点击更新操作"""
    if not EXECUTE_MULTI_PAGE_UPDATE:
        print("\n多页面更新功能已禁用。如需启用，请设置 EXECUTE_MULTI_PAGE_UPDATE = True\n")
        return True
    
    print("\n===== 开始执行多页面更新操作 =====\n")
    
    try:
        # 1. 文章列表页面 - aritcle-list
        article_page = f"{base_url}/frontend/page/aritcle-list"
        print(f"\n[1/3] 访问文章列表页面: {article_page}")
        driver.get(article_page)
        time.sleep(3)
        
        # 依次点击按钮
        article_buttons = ["更新公共样式", "更新blog全部列表页", "更新blog全部详情页"]
        for btn_text in article_buttons:
            if not click_button_with_confirmation(driver, btn_text, article_page):
                print(f"\n❌ 在文章页面点击 '{btn_text}' 失败，中止操作")
                return False
            time.sleep(2)  # 按钮之间等待
        
        # 2. FAQ列表页面 - faq-list
        faq_page = f"{base_url}/frontend/page/faq-list"
        print(f"\n[2/3] 访问FAQ列表页面: {faq_page}")
        driver.get(faq_page)
        time.sleep(3)
        
        # 依次点击按钮
        faq_buttons = ["更新公共样式", "更新faq全部列表页", "更新faq全部详情页"]
        for btn_text in faq_buttons:
            if not click_button_with_confirmation(driver, btn_text, faq_page):
                print(f"\n❌ 在FAQ页面点击 '{btn_text}' 失败，中止操作")
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
                # 尝试找到至少一个按钮，确认页面是否正确加载
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(., '更新公共样式')]"))
                )
                print("新闻页面存在，继续执行")
                
                # 依次点击按钮
                pressroom_buttons = ["更新公共样式", "更新pressroom全部列表页", "更新pressroom全部详情页"]
                for btn_text in pressroom_buttons:
                    if not click_button_with_confirmation(driver, btn_text, pressroom_page):
                        print(f"\n❌ 在新闻页面点击 '{btn_text}' 失败，中止操作")
                        return False
                    time.sleep(2)  # 按钮之间等待
                
            except (TimeoutException, NoSuchElementException):
                print("新闻页面不存在或没有找到预期按钮，跳过该页面")
        
        except Exception as e:
            print(f"访问新闻页面时出错: {e}")
            print("跳过新闻页面更新")
        
        print("\n✅ 多页面更新操作全部完成!")
        return True
        
    except Exception as e:
        print(f"\n❌ 多页面更新过程中出错: {e}")
        traceback.print_exc()
        return False

def process_site(driver, site_url, site_label=None):
    """处理单个站点的登录和更新操作"""
    try:
        label_info = f" [{site_label}]" if site_label else ""
        print(f"\n===== 开始处理站点{label_info}: {site_url} =====")
        
        # 从URL中提取基础URL
        base_url = '/'.join(site_url.split('/')[:3])  # 获取 http(s)://domain.com 部分
        
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
        
        # 检查是否需要登录 (如果存在用户名输入框)
        login_fields = driver.find_elements(By.CSS_SELECTOR, "input[placeholder='User Name']")
        if login_fields and any(field.is_displayed() for field in login_fields):
            print("检测到登录页面，执行登录...")
            try:
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
                login_success = wait_and_click(driver, "//button[contains(., 'login')]", By.XPATH, 10, "登录按钮")
                if not login_success:
                    # 尝试查找提交按钮的其他方式
                    print("尝试其他方式查找登录按钮...")
                    login_buttons = driver.find_elements(By.TAG_NAME, "button")
                    for button in login_buttons:
                        if button.is_displayed() and button.is_enabled():
                            try:
                                button.click()
                                print("点击了可能的登录按钮")
                                break
                            except:
                                continue
                
                print("等待登录完成...")
                time.sleep(5)  # 增加登录等待时间
                
                # 检查是否仍在登录页面
                login_fields_after = driver.find_elements(By.CSS_SELECTOR, "input[placeholder='User Name']")
                if login_fields_after and any(field.is_displayed() for field in login_fields_after):
                    print("登录似乎失败，仍在登录页面")
                    take_screenshot(driver, "login_failed")
                    return False
                
                # 重新导航到目标页面
                print("重新导航到目标页面...")
                driver.get(site_url)
                time.sleep(3)  # 等待页面加载
            except Exception as e:
                print(f"登录过程中出错: {e}")
                take_screenshot(driver, "login_error")
                return False
        else:
            print("已登录，无需重新登录")
        
        # 检查是否需要执行多页面更新
        if EXECUTE_MULTI_PAGE_UPDATE:
            # 执行多页面更新操作
            multi_page_result = perform_multi_page_updates(driver, base_url)
            if not multi_page_result:
                print(f"\n❌ 站点{label_info} 多页面更新操作失败")
                return False
            print(f"\n✅ 站点{label_info} 多页面更新操作成功完成")
            return True
            
        # 如果不执行多页面更新，执行单一按钮更新
        # 寻找并点击"更新公共样式"按钮
        print("寻找更新按钮...")
        try:
            # 尝试多种方式查找更新按钮
            update_button_found = False
            
            # 方法1：XPath
            try:
                update_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., '更新公共样式')]"))
                )
                print("找到更新按钮(XPath)")
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
                            print("找到更新按钮(遍历按钮)")
                            break
                    except:
                        continue
            
            if not update_button_found:
                print("未找到更新按钮，尝试截图当前页面...")
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
                    print(f"点击更新按钮失败: {click_error}")
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
                print("确认按钮已点击，检查部署状态...")
                deployment_result = check_deployment_status(driver, site_url)
                return deployment_result
            else:
                print("\n===================================")
                print(f"⚠️ 站点{label_info} 无法点击确认按钮，部署可能未启动。")
                print("===================================\n")
                take_screenshot(driver, "no_confirmation_button")
                return False
                
        except Exception as e:
            print(f"\n❌ 站点{label_info} 更新过程出错: {e}")
            take_screenshot(driver, "update_process_error")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"\n❌ 站点{label_info} 处理过程中出现错误: {e}")
        take_screenshot(driver, "process_site_error")
        traceback.print_exc()
        return False
    
    return None  # 默认返回未知状态

def load_sites_from_file(file_path, include_sites=None, exclude_sites=None):
    """从文件加载站点URL列表
    
    Args:
        file_path: 文件路径
        include_sites: 需要包含的站点标识列表，如 ['tw', 'en']
        exclude_sites: 需要排除的站点标识列表，如 ['en']
        
    Returns:
        dict: 含站点标识和URL的字典，如 {'tw': 'http://...', 'en': 'http://...'}
    """
    try:
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return None
            
        # 根据文件扩展名决定如何加载
        ext = os.path.splitext(file_path)[1].lower()
        sites_dict = {}
        
        if ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 处理新格式: urls 是一个字典
                if isinstance(data, dict) and 'urls' in data and isinstance(data['urls'], dict):
                    sites_dict = data['urls']
                    print(f"从JSON文件加载了 {len(sites_dict)} 个站点")
                
                # 处理旧格式: urls 是一个列表
                elif isinstance(data, dict) and 'urls' in data and isinstance(data['urls'], list):
                    urls_list = data['urls']
                    # 使用索引作为键
                    for i, url in enumerate(urls_list):
                        sites_dict[f"site{i+1}"] = url
                    print(f"从JSON文件加载了 {len(sites_dict)} 个站点 (旧格式转换)")
                
                # 处理直接的列表
                elif isinstance(data, list):
                    # 使用索引作为键
                    for i, url in enumerate(data):
                        sites_dict[f"site{i+1}"] = url
                    print(f"从JSON文件加载了 {len(sites_dict)} 个站点 (列表格式)")
                
                else:
                    print("JSON格式不正确，应为URL字典、URL列表或包含'urls'键的对象")
                    return None
                
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                # 去除空行和空格，使用行号作为键
                lines = [line.strip() for line in f if line.strip()]
                for i, url in enumerate(lines):
                    sites_dict[f"site{i+1}"] = url
                print(f"从文本文件加载了 {len(sites_dict)} 个站点")
        else:
            print(f"不支持的文件类型: {ext}")
            return None
            
        # 应用包含和排除过滤
        filtered_dict = {}
        
        if include_sites:
            # 只包含指定的站点
            include_list = include_sites.split(',')
            print(f"仅包含这些站点: {include_list}")
            for site_id in include_list:
                if site_id in sites_dict:
                    filtered_dict[site_id] = sites_dict[site_id]
                else:
                    print(f"警告: 指定包含的站点 '{site_id}' 不存在")
        
        elif exclude_sites:
            # 排除指定的站点
            exclude_list = exclude_sites.split(',')
            print(f"排除这些站点: {exclude_list}")
            for site_id, url in sites_dict.items():
                if site_id not in exclude_list:
                    filtered_dict[site_id] = url
        
        else:
            # 不过滤，使用所有站点
            filtered_dict = sites_dict
        
        print(f"过滤后保留了 {len(filtered_dict)} 个站点")
        
        return filtered_dict
        
    except Exception as e:
        print(f"加载站点文件时出错: {e}")
        traceback.print_exc()
        return None

def automate_vidnoz(sites_dict=None):
    """批量处理多个站点的主函数"""
    if sites_dict is None or not sites_dict:
        print("没有提供有效的站点列表")
        return {}
    
    # 显示待处理站点
    print(f"准备处理 {len(sites_dict)} 个站点:")
    for i, (site_id, url) in enumerate(sites_dict.items(), 1):
        print(f"{i}. [{site_id}] {url}")
    print("\n")
    
    # 显示多页面更新设置状态
    if EXECUTE_MULTI_PAGE_UPDATE:
        print("⚠️ 多页面更新功能已启用，将执行多页面按钮点击序列")
    else:
        print("ℹ️ 多页面更新功能已禁用，仅执行常规公共样式更新")
    
    # Chrome 选项设置
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # 添加忽略SSL证书错误选项
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    # 添加禁用infobars选项
    chrome_options.add_argument("--disable-infobars")
    # 添加禁用扩展选项
    chrome_options.add_argument("--disable-extensions")
    # 设置窗口大小，确保元素可见
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 添加实验性选项
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    print("设置 Chrome 驱动...")
    driver = webdriver.Chrome(options=chrome_options)
    
    # 最大化窗口以确保所有元素可见
    driver.maximize_window()
    
    results = {}
    try:
        # 处理每个站点
        for i, (site_id, site_url) in enumerate(sites_dict.items(), 1):
            print(f"\n[{i}/{len(sites_dict)}] 处理站点 [{site_id}]: {site_url}")
            result = process_site(driver, site_url, site_id)
            results[site_id] = {
                'url': site_url,
                'result': result
            }
            
            # 站点之间稍作暂停
            if i < len(sites_dict):
                print(f"等待 5 秒后继续下一个站点...")
                time.sleep(5)
    
    except Exception as e:
        print(f"\n❌ 批量处理过程中出现错误: {e}")
        traceback.print_exc()
    
    finally:
        # 关闭浏览器
        print("关闭浏览器...")
        driver.quit()
        
        # 显示汇总结果
        print("\n===== 批量处理结果汇总 =====")
        successful = sum(1 for site in results.values() if site['result'] is True)
        failed = sum(1 for site in results.values() if site['result'] is False)
        unknown = sum(1 for site in results.values() if site['result'] is None)
        
        print(f"总站点数: {len(results)}")
        print(f"成功: {successful}")
        print(f"失败: {failed}")
        print(f"状态未知: {unknown}")
        
        print("\n详细结果:")
        for site_id, site_info in results.items():
            status = "✅ 成功" if site_info['result'] is True else "❌ 失败" if site_info['result'] is False else "⚠️ 未知"
            print(f"{status}: [{site_id}] {site_info['url']}")
        
        print("\n程序执行完毕。")
        
        return results

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Vidnoz站点自动化工具')
    parser.add_argument('file', nargs='?', help='站点列表文件路径 (.json 或 .txt)')
    parser.add_argument('--include', help='仅包含指定的站点，以逗号分隔，如 tw,en')
    parser.add_argument('--exclude', help='排除指定的站点，以逗号分隔，如 en')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    if args.file:
        print(f"从文件加载站点列表: {args.file}")
        
        if args.include and args.exclude:
            print("错误: --include 和 --exclude 选项不能同时使用")
            sys.exit(1)
        
        sites = load_sites_from_file(
            args.file,
            include_sites=args.include,
            exclude_sites=args.exclude
        )
        
        if sites:
            automate_vidnoz(sites)
        else:
            print("无法从文件加载站点或过滤后没有站点")
    else:
        print("未提供站点列表文件，请指定 .json 或 .txt 文件")
        sys.exit(1) 