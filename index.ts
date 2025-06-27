const WebSocket = require('ws');
const { exec } = require('child_process');
const fetch = require('node-fetch');

// 类型定义
interface Target {
  type: string;
  webSocketDebuggerUrl: string;
  id: string;
  title: string;
  url: string;
}

interface Metric {
  name: string;
  value: number;
}

interface PerformanceData {
  performanceMetrics: Metric[] | null;
  navigationEntry: any;
}

// 启动Chrome并启用远程调试
const launchChrome = () => {
  return new Promise((resolve, reject) => {
    const os = require('os');
    const path = require('path');
    
    const chromePath = 
      process.platform === 'win32' ? 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' :
      process.platform === 'darwin' ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' :
      '/usr/bin/google-chrome';
    
    // 创建临时目录
    const tempDir = path.join(os.tmpdir(), `chrome-remote-${Date.now()}`);
    
    const cmd = `"${chromePath}" --remote-debugging-port=9222 --no-first-run --no-default-browser-check --user-data-dir="${tempDir}"`;
    
    const child = exec(cmd, (error, stdout, stderr) => {
      if (error) {
        reject(new Error(`启动Chrome失败: ${error.message}`));
        return;
      }
      if (stderr) {
        console.warn(`Chrome输出: ${stderr}`);
      }
    });
    
    resolve(child);
  });
};

// 获取调试会话
const getDebugSession = async () => {
  // 等待Chrome完全启动，最多重试10次
  for (let i = 0; i < 10; i++) {
    try {
      const response = await fetch('http://localhost:9222/json');
      const targets = await response.json();
      const pageTarget = targets.find((target: any) => target.type === 'page');
      
      if (pageTarget) {
        return pageTarget;
      }
      
      // 如果没有找到页面目标，等待1秒后重试
      console.log(`等待Chrome启动... (${i + 1}/10)`);
      await new Promise(resolve => setTimeout(resolve, 1000));
    } catch (error) {
      // 连接失败，等待1秒后重试
      console.log(`等待Chrome启动... (${i + 1}/10)`);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  
  throw new Error('Chrome启动超时或未找到可用的页面目标');
};

// 收集性能数据
const collectPerformanceMetrics = async (target: Target): Promise<PerformanceData> => {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    let commandId = 0;
    let performanceMetrics: Metric[] | null = null;
    let navigationEntry: any = null;
    let dataCollected = false;
    
    const cleanup = () => {
      if (!dataCollected) {
        dataCollected = true;
        ws.close();
        resolve({ performanceMetrics, navigationEntry });
      }
    };
    
    ws.on('open', () => {
      console.log('WebSocket连接已建立');
      
      // 启用Runtime域
      ws.send(JSON.stringify({
        id: ++commandId,
        method: 'Runtime.enable'
      }));
      
      // 启用性能指标收集
      ws.send(JSON.stringify({
        id: ++commandId,
        method: 'Performance.enable'
      }));
      
      // 启用页面加载监听
      ws.send(JSON.stringify({
        id: ++commandId,
        method: 'Page.enable'
      }));
      
      // 导航到目标URL
      ws.send(JSON.stringify({
        id: ++commandId,
        method: 'Page.navigate',
        params: { url: 'https://www.baidu.com' }
      }));
    });
    
    ws.on('message', (data: any) => {
      const message = JSON.parse(data.toString());
      console.log('收到消息:', message.method || 'response');
      
      // 处理命令响应
      if (message.result && message.id) {
        // 如果是Performance.getMetrics的响应
        if (message.result.metrics) {
          console.log('收到性能指标数据:', message.result.metrics.length, '个指标');
          performanceMetrics = message.result.metrics;
        }
      }
      
      // 处理事件
      if (message.method === 'Page.loadEventFired') {
        console.log('页面加载完成，等待3秒后获取性能数据...');
        
        // 等待3秒让所有性能指标稳定后再收集
        setTimeout(() => {
          // 获取性能指标
          ws.send(JSON.stringify({
            id: ++commandId,
            method: 'Performance.getMetrics'
          }));
          
          // 使用更现代的Performance API获取数据
          ws.send(JSON.stringify({
            id: ++commandId,
            method: 'Runtime.evaluate',
            params: {
              expression: `
                (function() {
                  const perfEntries = performance.getEntriesByType('navigation')[0];
                  const paintEntries = performance.getEntriesByType('paint');
                  const layoutShiftEntries = performance.getEntriesByType('layout-shift');
                  
                  const result = {
                    // Navigation Timing
                    navigationStart: perfEntries ? perfEntries.fetchStart : performance.timing.navigationStart,
                    domContentLoadedEventStart: perfEntries ? perfEntries.domContentLoadedEventStart : performance.timing.domContentLoadedEventStart,
                    domContentLoadedEventEnd: perfEntries ? perfEntries.domContentLoadedEventEnd : performance.timing.domContentLoadedEventEnd,
                    loadEventStart: perfEntries ? perfEntries.loadEventStart : performance.timing.loadEventStart,
                    loadEventEnd: perfEntries ? perfEntries.loadEventEnd : performance.timing.loadEventEnd,
                    responseEnd: perfEntries ? perfEntries.responseEnd : performance.timing.responseEnd,
                    domInteractive: perfEntries ? perfEntries.domInteractive : performance.timing.domInteractive,
                    
                    // Paint Timing
                    firstPaint: paintEntries.find(e => e.name === 'first-paint')?.startTime || null,
                    firstContentfulPaint: paintEntries.find(e => e.name === 'first-contentful-paint')?.startTime || null,
                    
                    // Cumulative Layout Shift
                    cumulativeLayoutShift: layoutShiftEntries.reduce((sum, entry) => sum + entry.value, 0),
                    
                    // LCP (需要observer，这里先用占位符)
                    largestContentfulPaint: null,
                    
                    // 其他有用的指标
                    domComplete: perfEntries ? perfEntries.domComplete : performance.timing.domComplete,
                    transferSize: perfEntries ? perfEntries.transferSize : null,
                    encodedBodySize: perfEntries ? perfEntries.encodedBodySize : null,
                    decodedBodySize: perfEntries ? perfEntries.decodedBodySize : null
                  };
                  
                  return JSON.stringify(result);
                })()
              `,
              returnByValue: true
            }
          }));
          
          // 获取LCP（需要使用PerformanceObserver模拟）
          ws.send(JSON.stringify({
            id: ++commandId,
            method: 'Runtime.evaluate',
            params: {
              expression: `
                (function() {
                  try {
                    const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
                    return JSON.stringify({
                      largestContentfulPaint: lcpEntries.length > 0 ? lcpEntries[lcpEntries.length - 1].startTime : null
                    });
                  } catch (e) {
                    return JSON.stringify({ largestContentfulPaint: null });
                  }
                })()
              `,
              returnByValue: true
            }
          }));
        }, 3000);
        
        // 10秒后强制结束
        setTimeout(() => {
          console.log('数据收集超时，强制结束');
          cleanup();
        }, 10000);
      }
      
      // 处理Runtime.evaluate的响应
      if (message.result && message.result.value && typeof message.result.value === 'string') {
        try {
          const data = JSON.parse(message.result.value);
          console.log('收到JavaScript执行结果');
          
          // 如果是完整的性能数据
          if (data.navigationStart !== undefined) {
            navigationEntry = data;
            console.log('收到完整的性能数据');
          }
          
          // 如果是LCP数据
          if (data.largestContentfulPaint !== undefined && navigationEntry) {
            navigationEntry.largestContentfulPaint = data.largestContentfulPaint;
            console.log('收到LCP数据');
          }
          
          // 如果已经收到了数据，延迟1秒后结束
          if ((performanceMetrics && performanceMetrics.length > 0) || navigationEntry) {
            setTimeout(cleanup, 1000);
          }
        } catch (e) {
          console.log('JSON解析错误:', e);
        }
      }
    });
    
    ws.on('close', () => {
      console.log('WebSocket连接已关闭');
      if (!dataCollected) {
        dataCollected = true;
        resolve({ performanceMetrics, navigationEntry });
      }
    });
    
    ws.on('error', (error: any) => {
      console.error('WebSocket错误:', error);
      if (!dataCollected) {
        dataCollected = true;
        reject(error);
      }
    });
    
    // 10秒超时保护
    setTimeout(() => {
      if (!dataCollected) {
        console.log('总体超时，强制结束');
        cleanup();
      }
    }, 10000);
  });
};

// 主函数
(async () => {
  try {
    console.log('正在启动Chrome...');
    const chromeProcess = await launchChrome();
    
    // 等待Chrome完全启动
    console.log('等待Chrome启动...');
    await new Promise(resolve => setTimeout(resolve, 5000)); // 增加等待时间到5秒
    
    console.log('正在连接调试会话...');
    const debugSession = await getDebugSession();
    
    console.log('正在收集性能数据...');
    const { performanceMetrics, navigationEntry } = await collectPerformanceMetrics(debugSession);
    
    // 处理并打印性能数据
    if (performanceMetrics && performanceMetrics.length > 0) {
      const metricsMap: { [key: string]: number } = performanceMetrics.reduce((acc: { [key: string]: number }, metric: Metric) => {
        acc[metric.name] = metric.value;
        return acc;
      }, {});
      
      console.log('\n===== Chrome DevTools 性能指标 =====');
      console.log(`Timestamp: ${metricsMap['Timestamp'] || 'N/A'}`);
      console.log(`Documents: ${metricsMap['Documents'] || 'N/A'}`);
      console.log(`Frames: ${metricsMap['Frames'] || 'N/A'}`);
      console.log(`JSEventListeners: ${metricsMap['JSEventListeners'] || 'N/A'}`);
      console.log(`Nodes: ${metricsMap['Nodes'] || 'N/A'}`);
      console.log(`LayoutCount: ${metricsMap['LayoutCount'] || 'N/A'}`);
      console.log(`RecalcStyleCount: ${metricsMap['RecalcStyleCount'] || 'N/A'}`);
      
      console.log('\n所有可用指标:');
      performanceMetrics.forEach((metric: Metric) => {
        console.log(`${metric.name}: ${metric.value}`);
      });
    } else {
      console.log('未收集到Chrome DevTools性能指标数据');
    }
    
    // 显示性能时间数据
    if (navigationEntry) {
      console.log('\n===== 页面性能时间指标 =====');
      
      // 计算各项时间指标
      const navigationStart = navigationEntry.navigationStart || 0;
      const firstPaint = navigationEntry.firstPaint;
      const firstContentfulPaint = navigationEntry.firstContentfulPaint;
      const largestContentfulPaint = navigationEntry.largestContentfulPaint;
      const domContentLoaded = navigationEntry.domContentLoadedEventEnd - navigationStart;
      const loadComplete = navigationEntry.loadEventEnd - navigationStart;
      const domInteractive = navigationEntry.domInteractive - navigationStart;
      
      console.log(`首次绘制 (FP): ${firstPaint ? Math.round(firstPaint) + 'ms' : 'N/A'}`);
      console.log(`首次内容绘制 (FCP): ${firstContentfulPaint ? Math.round(firstContentfulPaint) + 'ms' : 'N/A'}`);
      console.log(`最大内容绘制 (LCP): ${largestContentfulPaint ? Math.round(largestContentfulPaint) + 'ms' : 'N/A'}`);
      console.log(`累积布局偏移 (CLS): ${navigationEntry.cumulativeLayoutShift || 0}`);
      console.log(`DOM交互时间: ${domInteractive ? Math.round(domInteractive) + 'ms' : 'N/A'}`);
      console.log(`DOM内容加载完成: ${domContentLoaded ? Math.round(domContentLoaded) + 'ms' : 'N/A'}`);
      console.log(`页面完全加载: ${loadComplete ? Math.round(loadComplete) + 'ms' : 'N/A'}`);
      
      // 显示网络相关指标
      if (navigationEntry.transferSize) {
        console.log(`\n===== 网络性能指标 =====`);
        console.log(`传输大小: ${Math.round(navigationEntry.transferSize / 1024)} KB`);
        console.log(`编码大小: ${navigationEntry.encodedBodySize ? Math.round(navigationEntry.encodedBodySize / 1024) + ' KB' : 'N/A'}`);
        console.log(`解码大小: ${navigationEntry.decodedBodySize ? Math.round(navigationEntry.decodedBodySize / 1024) + ' KB' : 'N/A'}`);
      }
      
      console.log('\n===== 原始导航数据 =====');
      console.log(JSON.stringify(navigationEntry, null, 2));
    } else {
      console.log('未收集到性能时间数据');
    }
    
    // 关闭Chrome进程（可选）
    // chromeProcess.kill();
    
  } catch (error) {
    console.error('性能检测失败:', error);
  }
})();