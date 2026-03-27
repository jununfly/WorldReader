const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  
  try {
    await page.goto('https://mp.weixin.qq.com/s/tpX87yUoDo3-vGdR9u1vCA', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    
    // 检查是否有验证页面
    const isCaptcha = await page.$('.weui-msg__title');
    if (isCaptcha) {
      const captchaText = await page.$eval('.weui-msg__title', el => el.innerText);
      console.log('需要验证:', captchaText);
      await browser.close();
      return;
    }
    
    // 提取标题
    const title = await page.$eval('#activity-name', el => el.innerText.trim()).catch(() => '未知标题');
    
    // 提取正文
    const content = await page.$eval('#js_content', el => el.innerText.trim()).catch(() => {
      // 尝试其他选择器
      return page.$eval('.rich_media_content', el => el.innerText.trim()).catch(() => '无法提取内容');
    });
    
    // 提取作者
    const author = await page.$eval('#js_name', el => el.innerText.trim()).catch(() => '未知作者');
    
    // 提取发布时间
    const publishTime = await page.$eval('#publish_time', el => el.innerText.trim()).catch(() => '未知时间');
    
    console.log('=== 文章信息 ===');
    console.log('标题:', title);
    console.log('作者:', author);
    console.log('发布时间:', publishTime);
    console.log('\n=== 正文内容 ===');
    console.log(content);
    
    // 截图保存
    await page.screenshot({ path: '/home/admin/.openclaw/workspace/wechat-article.png', fullPage: true });
    console.log('\n截图已保存：wechat-article.png');
    
  } catch (error) {
    console.error('错误:', error.message);
  }
  
  await browser.close();
})();
