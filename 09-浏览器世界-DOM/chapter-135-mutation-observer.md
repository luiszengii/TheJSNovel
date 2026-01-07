《第 135 次记录：DOM 变化的窥探者 —— MutationObserver 监听机制》

## 第三方脚本入侵事件

周一上午 10 点 15 分，你的 Slack 弹出一条紧急消息："首页的布局又乱了，广告脚本把我们的导航栏挤到下面去了！"

你立刻打开线上页面。果然，页面顶部的导航栏被推到了页面底部，顶部多出了一个巨大的广告横幅。你打开 DevTools，检查 DOM 结构 —— 在 `<body>` 的第一个子元素位置，多了一个 `<div class="ad-banner">` 节点。

"这是怎么插进来的？" 你查看了项目代码，没有任何地方写了这段广告代码。你检查了 Network 面板，发现页面加载了一个第三方脚本 `analytics-plus.js`，这是市场部上周要求添加的"增强版统计脚本"。

你在控制台输入 `document.body.firstElementChild`，确认了那个广告节点确实存在。但问题是：这个节点是什么时候被插入的？是在页面加载时还是用户交互后？你需要一个方法来监控 DOM 的变化。

前端架构师老赵走过来："你需要用 MutationObserver。它就像一个 DOM 警卫，能实时监控 DOM 树的任何变化。"

## 设置 DOM 监听器

老赵展示了 MutationObserver 的基本用法：

```javascript
// 创建观察器实例
const observer = new MutationObserver((mutations) => {
  mutations.forEach(mutation => {
    console.log('DOM 发生了变化:', mutation);
    console.log('变化类型:', mutation.type);
    console.log('目标节点:', mutation.target);
  });
});

// 配置观察选项
const config = {
  childList: true,      // 观察子节点的添加和删除
  attributes: true,     // 观察属性变化
  characterData: true,  // 观察文本内容变化
  subtree: true,        // 观察所有后代节点
  attributeOldValue: true,    // 记录属性的旧值
  characterDataOldValue: true // 记录文本的旧值
};

// 开始观察 body 元素
observer.observe(document.body, config);

// 测试：添加一个元素
const div = document.createElement('div');
div.textContent = '测试内容';
document.body.appendChild(div);

// 控制台输出：
// DOM 发生了变化: MutationRecord { type: 'childList', ... }
// 变化类型: childList
// 目标节点: <body>...</body>
```

你立刻写了一个监控脚本，部署到测试环境：

```javascript
const domWatcher = new MutationObserver((mutations) => {
  mutations.forEach(mutation => {
    if (mutation.type === 'childList') {
      mutation.addedNodes.forEach(node => {
        if (node.nodeType === 1) { // 元素节点
          console.log('新增节点:', node);
          console.log('节点位置:', node.parentElement);
          console.log('节点 HTML:', node.outerHTML.slice(0, 100));

          // 检查是否是广告节点
          if (node.classList.contains('ad-banner')) {
            console.error('⚠️ 检测到广告节点被插入！');
            console.trace('调用堆栈'); // 查看是谁插入的
          }
        }
      });

      mutation.removedNodes.forEach(node => {
        if (node.nodeType === 1) {
          console.log('移除节点:', node);
        }
      });
    }
  });
});

// 开始监控整个 body
domWatcher.observe(document.body, {
  childList: true,
  subtree: true
});
```

刷新页面，控制台立刻输出了关键信息：

```
新增节点: <div class="ad-banner">...</div>
节点位置: <body>
节点 HTML: <div class="ad-banner" style="width: 100%; height: 120px; background: #f0f0f0;">...
⚠️ 检测到广告节点被插入！
调用堆栈:
  at analytics-plus.js:247
  at analytics-plus.js:1523
```

"找到了！" 你兴奋地说，"是 `analytics-plus.js` 的第 247 行插入的广告！"

## 监控的三种变化类型

老赵展示了 MutationObserver 能监控的三种变化：

```javascript
const observer = new MutationObserver((mutations) => {
  mutations.forEach(mutation => {
    switch (mutation.type) {
      case 'childList':
        // 子节点变化：添加或删除子节点
        console.log('子节点变化');
        console.log('添加的节点:', mutation.addedNodes);
        console.log('移除的节点:', mutation.removedNodes);
        console.log('前一个兄弟节点:', mutation.previousSibling);
        console.log('后一个兄弟节点:', mutation.nextSibling);
        break;

      case 'attributes':
        // 属性变化：属性被添加、修改或删除
        console.log('属性变化');
        console.log('变化的属性名:', mutation.attributeName);
        console.log('属性的旧值:', mutation.oldValue);
        console.log('属性的新值:', mutation.target.getAttribute(mutation.attributeName));
        break;

      case 'characterData':
        // 文本变化：文本节点的内容变化
        console.log('文本内容变化');
        console.log('文本的旧值:', mutation.oldValue);
        console.log('文本的新值:', mutation.target.textContent);
        break;
    }
  });
});

// 测试所有三种变化
const testDiv = document.createElement('div');
testDiv.textContent = '原始文本';
document.body.appendChild(testDiv);

observer.observe(document.body, {
  childList: true,
  attributes: true,
  characterData: true,
  subtree: true,
  attributeOldValue: true,
  characterDataOldValue: true
});

// 1. 测试子节点变化
const span = document.createElement('span');
testDiv.appendChild(span); // 触发 childList 变化

// 2. 测试属性变化
testDiv.setAttribute('data-test', 'value1'); // 触发 attributes 变化
testDiv.setAttribute('data-test', 'value2'); // 再次触发

// 3. 测试文本变化
testDiv.firstChild.textContent = '新文本'; // 触发 characterData 变化
```

老赵特别强调："MutationObserver 是异步的，所有变化会被批量收集，然后在微任务队列中统一处理。这样可以避免频繁触发回调，提高性能。"

```javascript
const observer = new MutationObserver((mutations) => {
  console.log('回调触发，收到', mutations.length, '个变化记录');
});

observer.observe(document.body, { childList: true });

// 连续进行 3 次 DOM 操作
console.log('开始操作 1');
document.body.appendChild(document.createElement('div'));

console.log('开始操作 2');
document.body.appendChild(document.createElement('span'));

console.log('开始操作 3');
document.body.appendChild(document.createElement('p'));

console.log('所有操作完成');

// 控制台输出顺序：
// 开始操作 1
// 开始操作 2
// 开始操作 3
// 所有操作完成
// 回调触发，收到 3 个变化记录

// 说明：回调在所有同步代码执行完毕后才触发（微任务）
```

## 实战：防御第三方脚本污染

老赵帮你设计了一个完整的 DOM 污染防御系统：

```javascript
class DOMGuard {
  constructor() {
    this.observer = null;
    this.whitelist = new Set(); // 白名单节点
    this.violations = []; // 违规记录
    this.init();
  }

  init() {
    this.observer = new MutationObserver((mutations) => {
      this.handleMutations(mutations);
    });

    // 开始监控整个文档
    this.observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class', 'style', 'id'] // 只监控特定属性
    });

    console.log('DOM 防护系统已启动');
  }

  handleMutations(mutations) {
    mutations.forEach(mutation => {
      if (mutation.type === 'childList') {
        this.checkAddedNodes(mutation.addedNodes);
      } else if (mutation.type === 'attributes') {
        this.checkAttributeChange(mutation);
      }
    });
  }

  checkAddedNodes(nodes) {
    nodes.forEach(node => {
      if (node.nodeType !== 1) return; // 只检查元素节点

      // 检查是否在白名单中
      if (this.whitelist.has(node)) return;

      // 检查危险特征
      const isDangerous =
        node.classList.contains('ad-banner') ||
        node.classList.contains('popup') ||
        node.style.position === 'fixed' ||
        node.style.zIndex > 9000;

      if (isDangerous) {
        console.warn('⚠️ 检测到可疑节点:', node);

        // 记录违规
        this.violations.push({
          type: 'suspicious-node',
          node: node,
          timestamp: Date.now(),
          stack: new Error().stack
        });

        // 可选：自动移除
        // node.remove();

        // 或者：标记为可疑
        node.setAttribute('data-dom-guard', 'suspicious');
        node.style.outline = '2px solid red';
      }
    });
  }

  checkAttributeChange(mutation) {
    const element = mutation.target;
    const attrName = mutation.attributeName;
    const oldValue = mutation.oldValue;
    const newValue = element.getAttribute(attrName);

    // 检查样式被恶意修改
    if (attrName === 'style') {
      const hasFixedPosition = newValue.includes('position: fixed') ||
                               newValue.includes('position:fixed');

      if (hasFixedPosition && !oldValue.includes('fixed')) {
        console.warn('⚠️ 元素被修改为 fixed 定位:', element);

        this.violations.push({
          type: 'style-hijack',
          element: element,
          attribute: attrName,
          oldValue: oldValue,
          newValue: newValue,
          timestamp: Date.now()
        });
      }
    }
  }

  addToWhitelist(node) {
    this.whitelist.add(node);
  }

  getViolations() {
    return this.violations;
  }

  disconnect() {
    if (this.observer) {
      this.observer.disconnect();
      console.log('DOM 防护系统已关闭');
    }
  }
}

// 启动防护系统
const guard = new DOMGuard();

// 查看违规记录
setTimeout(() => {
  const violations = guard.getViolations();
  console.log('发现', violations.length, '个违规操作');
  violations.forEach(v => {
    console.log('违规类型:', v.type);
    console.log('时间:', new Date(v.timestamp).toLocaleTimeString());
  });
}, 5000);
```

## 性能优化与停止观察

老赵展示了如何优化 MutationObserver 的性能：

```javascript
// 1. 限制观察范围
// ❌ 不好：观察整个文档
observer.observe(document.documentElement, {
  childList: true,
  subtree: true
});

// ✅ 好：只观察需要的区域
const container = document.querySelector('.content-area');
observer.observe(container, {
  childList: true,
  subtree: true
});

// 2. 使用防抖减少处理频率
class ThrottledObserver {
  constructor(callback, delay = 100) {
    this.callback = callback;
    this.delay = delay;
    this.timeout = null;
    this.pendingMutations = [];

    this.observer = new MutationObserver((mutations) => {
      this.pendingMutations.push(...mutations);

      clearTimeout(this.timeout);
      this.timeout = setTimeout(() => {
        this.callback(this.pendingMutations);
        this.pendingMutations = [];
      }, this.delay);
    });
  }

  observe(target, options) {
    this.observer.observe(target, options);
  }

  disconnect() {
    clearTimeout(this.timeout);
    this.observer.disconnect();
  }
}

// 使用防抖观察器
const throttledObserver = new ThrottledObserver((mutations) => {
  console.log('处理', mutations.length, '个变化（防抖后）');
}, 200);

throttledObserver.observe(document.body, {
  childList: true,
  subtree: true
});

// 3. 临时停止观察
const observer = new MutationObserver((mutations) => {
  console.log('DOM 变化:', mutations.length);
});

observer.observe(document.body, { childList: true });

// 执行大量 DOM 操作前，临时停止观察
function batchUpdate() {
  observer.disconnect(); // 停止观察

  // 执行大量 DOM 操作
  for (let i = 0; i < 1000; i++) {
    const div = document.createElement('div');
    document.body.appendChild(div);
  }

  // 操作完成后，重新开始观察
  observer.observe(document.body, { childList: true });
}

batchUpdate();

// 4. 完全停止并清理
function cleanup() {
  observer.disconnect(); // 停止观察
  observer = null; // 释放引用，允许垃圾回收
}
```

## 实际应用场景

老赵展示了几个实际应用场景：

```javascript
// 场景 1: 监控富文本编辑器内容变化
class ContentAutoSave {
  constructor(editor) {
    this.editor = editor;
    this.observer = new MutationObserver(() => {
      this.debouncedSave();
    });

    this.observer.observe(editor, {
      childList: true,
      characterData: true,
      subtree: true
    });
  }

  debouncedSave = debounce(() => {
    const content = this.editor.innerHTML;
    localStorage.setItem('draft', content);
    console.log('自动保存成功');
  }, 1000);
}

// 场景 2: 检测无限滚动加载的新内容
class InfiniteScrollMonitor {
  constructor(container) {
    this.container = container;
    this.observer = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
          if (node.classList && node.classList.contains('item')) {
            console.log('新增了一个列表项');
            this.processNewItem(node);
          }
        });
      });
    });

    this.observer.observe(container, { childList: true });
  }

  processNewItem(item) {
    // 为新添加的项目绑定事件
    item.addEventListener('click', () => {
      console.log('点击了:', item.textContent);
    });
  }
}

// 场景 3: 监控 SPA 路由变化导致的 DOM 更新
class SPANavigationTracker {
  constructor() {
    this.observer = new MutationObserver((mutations) => {
      const hasSignificantChange = mutations.some(m =>
        m.addedNodes.length > 5 || m.removedNodes.length > 5
      );

      if (hasSignificantChange) {
        console.log('检测到页面切换');
        this.trackPageView();
      }
    });

    this.observer.observe(document.querySelector('#app'), {
      childList: true,
      subtree: true
    });
  }

  trackPageView() {
    const currentPath = window.location.pathname;
    console.log('页面访问:', currentPath);
    // 发送统计数据
  }
}

// 场景 4: 开发者工具 - DOM 变化追踪
class DOMChangeTracker {
  constructor() {
    this.changes = [];
    this.observer = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        this.changes.push({
          type: mutation.type,
          target: mutation.target,
          timestamp: Date.now(),
          addedNodes: Array.from(mutation.addedNodes),
          removedNodes: Array.from(mutation.removedNodes)
        });
      });
    });

    this.observer.observe(document.body, {
      childList: true,
      attributes: true,
      characterData: true,
      subtree: true,
      attributeOldValue: true,
      characterDataOldValue: true
    });
  }

  getChangeHistory() {
    return this.changes;
  }

  exportHistory() {
    const json = JSON.stringify(this.changes, null, 2);
    console.log('DOM 变化历史:', json);
  }
}
```

下午 3 点，你完成了 DOM 防护系统的部署。系统成功拦截了第三方脚本的广告插入，并生成了详细的违规报告。你给市场部发了一份报告："analytics-plus.js 存在恶意代码，建议更换统计服务商。" 同时，你在团队 Wiki 上记录了这次事件，提醒大家谨慎选择第三方脚本。

---

## 技术档案：MutationObserver 核心机制

**规则 1: MutationObserver 是异步的微任务**

MutationObserver 的回调函数在微任务队列中执行，所有同步代码执行完毕后才会触发。多个 DOM 变化会被批量收集，然后一次性传递给回调函数。

```javascript
const observer = new MutationObserver((mutations) => {
  console.log('收到', mutations.length, '个变化');
});

observer.observe(document.body, { childList: true });

// 同步执行 3 个 DOM 操作
document.body.appendChild(document.createElement('div')); // 变化 1
document.body.appendChild(document.createElement('span')); // 变化 2
document.body.appendChild(document.createElement('p')); // 变化 3

console.log('同步代码执行完毕');

// 输出顺序：
// 同步代码执行完毕
// 收到 3 个变化

// 批量处理的优势：
// - 减少回调触发次数
// - 提高性能
// - 避免在 DOM 操作过程中触发回调
```

**规则 2: 三种变化类型的监听配置**

MutationObserver 可以监听三种类型的 DOM 变化，通过配置对象控制监听的内容和深度。

```javascript
const observer = new MutationObserver((mutations) => {
  // 处理变化
});

const config = {
  // 子节点变化：添加或删除子节点
  childList: true,

  // 属性变化：属性被添加、修改或删除
  attributes: true,
  attributeFilter: ['class', 'style'], // 只监听特定属性
  attributeOldValue: true, // 记录属性的旧值

  // 文本变化：文本节点的内容变化
  characterData: true,
  characterDataOldValue: true, // 记录文本的旧值

  // 是否监听所有后代节点（而非只监听直接子节点）
  subtree: true
};

observer.observe(document.body, config);

// 变化类型对应的 MutationRecord 字段：
// childList 变化：
//   - addedNodes: 新增的节点列表
//   - removedNodes: 移除的节点列表
//   - previousSibling: 前一个兄弟节点
//   - nextSibling: 后一个兄弟节点

// attributes 变化：
//   - attributeName: 变化的属性名
//   - oldValue: 属性的旧值（需要 attributeOldValue: true）

// characterData 变化：
//   - oldValue: 文本的旧值（需要 characterDataOldValue: true）
//   - target.textContent: 文本的新值
```

**规则 3: disconnect 停止观察并释放资源**

使用 `disconnect()` 方法停止观察，并确保释放观察器引用以允许垃圾回收。在不需要观察时及时停止可以提高性能。

```javascript
const observer = new MutationObserver((mutations) => {
  console.log('DOM 变化:', mutations.length);
});

observer.observe(document.body, { childList: true });

// 停止观察
observer.disconnect();

// 之后的 DOM 变化不会触发回调
document.body.appendChild(document.createElement('div')); // 不会触发

// 可以重新开始观察
observer.observe(document.body, { childList: true });

// 临时停止和恢复的场景：
function batchDOMUpdate() {
  observer.disconnect(); // 停止观察

  // 执行大量 DOM 操作
  for (let i = 0; i < 1000; i++) {
    document.body.appendChild(document.createElement('div'));
  }

  observer.observe(document.body, { childList: true }); // 恢复观察
}

// 完全清理：
observer.disconnect();
observer = null; // 释放引用
```

**规则 4: 限制观察范围提高性能**

只观察需要的 DOM 区域，而非整个文档。使用 `attributeFilter` 限制监听的属性，减少不必要的回调触发。

```javascript
// ❌ 性能差：观察整个文档的所有变化
const badObserver = new MutationObserver((mutations) => {
  // 会被频繁触发
});

badObserver.observe(document.documentElement, {
  childList: true,
  attributes: true,
  characterData: true,
  subtree: true
});

// ✅ 性能好：只观察特定区域的特定变化
const goodObserver = new MutationObserver((mutations) => {
  // 只在需要时触发
});

const targetContainer = document.querySelector('.content-area');

goodObserver.observe(targetContainer, {
  childList: true, // 只关心子节点变化
  attributeFilter: ['class', 'data-status'], // 只监听特定属性
  subtree: false // 不监听后代节点
});

// 性能优化建议：
// 1. 尽可能缩小观察范围
// 2. 只监听必要的变化类型
// 3. 使用 attributeFilter 限制属性监听
// 4. 考虑使用防抖减少回调频率
```

**规则 5: 使用防抖优化高频变化场景**

在 DOM 频繁变化的场景（如富文本编辑器、无限滚动），使用防抖减少回调处理频率，提高性能。

```javascript
class ThrottledObserver {
  constructor(callback, delay = 100) {
    this.callback = callback;
    this.delay = delay;
    this.timeout = null;
    this.pendingMutations = [];

    this.observer = new MutationObserver((mutations) => {
      // 收集所有变化
      this.pendingMutations.push(...mutations);

      // 防抖：延迟处理
      clearTimeout(this.timeout);
      this.timeout = setTimeout(() => {
        this.callback(this.pendingMutations);
        this.pendingMutations = [];
      }, this.delay);
    });
  }

  observe(target, options) {
    this.observer.observe(target, options);
  }

  disconnect() {
    clearTimeout(this.timeout);
    this.observer.disconnect();
  }
}

// 使用示例：富文本编辑器自动保存
const editor = document.querySelector('.editor');

const autoSaveObserver = new ThrottledObserver((mutations) => {
  console.log('处理', mutations.length, '个变化');
  const content = editor.innerHTML;
  localStorage.setItem('draft', content);
  console.log('自动保存成功');
}, 1000); // 1 秒防抖

autoSaveObserver.observe(editor, {
  childList: true,
  characterData: true,
  subtree: true
});

// 用户快速输入时：
// - 每次输入都会触发 MutationObserver
// - 但只有在停止输入 1 秒后才会执行保存
// - 避免频繁的保存操作
```

**规则 6: 实际应用场景的最佳实践**

根据不同场景选择合适的配置和优化策略，确保功能正确性的同时保持良好性能。

```javascript
// 场景 1: DOM 污染防御（监控第三方脚本）
class DOMGuard {
  constructor() {
    this.observer = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === 1 && this.isSuspicious(node)) {
            console.warn('检测到可疑节点:', node);
            this.handleViolation(node);
          }
        });
      });
    });

    this.observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  isSuspicious(node) {
    return node.classList.contains('ad-banner') ||
           node.style.position === 'fixed' ||
           node.style.zIndex > 9000;
  }

  handleViolation(node) {
    // 记录违规、标记节点、发送告警
    node.setAttribute('data-suspicious', 'true');
  }
}

// 场景 2: 富文本编辑器自动保存
class AutoSave {
  constructor(editor, saveInterval = 1000) {
    this.editor = editor;
    this.timeout = null;

    this.observer = new MutationObserver(() => {
      clearTimeout(this.timeout);
      this.timeout = setTimeout(() => this.save(), saveInterval);
    });

    this.observer.observe(editor, {
      childList: true,
      characterData: true,
      subtree: true
    });
  }

  save() {
    const content = this.editor.innerHTML;
    localStorage.setItem('draft', content);
  }
}

// 场景 3: 无限滚动内容监控
class InfiniteScrollMonitor {
  constructor(container) {
    this.observer = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
          if (node.classList?.contains('item')) {
            this.initializeItem(node);
          }
        });
      });
    });

    this.observer.observe(container, { childList: true });
  }

  initializeItem(item) {
    // 为新加载的项目绑定事件、懒加载图片等
  }
}

// 场景 4: SPA 路由变化追踪
class RouteChangeDetector {
  constructor() {
    this.observer = new MutationObserver((mutations) => {
      const hasSignificantChange = mutations.some(m =>
        m.addedNodes.length > 5 || m.removedNodes.length > 5
      );

      if (hasSignificantChange) {
        this.onRouteChange();
      }
    });

    this.observer.observe(document.querySelector('#app'), {
      childList: true,
      subtree: true
    });
  }

  onRouteChange() {
    console.log('页面切换到:', window.location.pathname);
    // 发送页面访问统计
  }
}
```

---

**记录者注**:

MutationObserver 是现代浏览器提供的强大 DOM 监控 API，它能实时监听 DOM 树的变化，包括子节点添加/删除、属性修改、文本内容变化。与旧的 Mutation Events 相比，MutationObserver 是异步的（微任务队列），批量处理变化，性能更高。

关键在于理解三种变化类型（childList、attributes、characterData）和配置选项（subtree、attributeFilter、oldValue）。通过限制观察范围、使用 attributeFilter、结合防抖优化，可以在保证功能的同时避免性能问题。实际应用场景包括 DOM 污染防御、富文本自动保存、无限滚动监控、SPA 路由追踪等。

记住：**MutationObserver 是异步微任务，批量处理变化；限制观察范围和监听类型提高性能；使用 disconnect 及时停止观察；根据场景选择合适的配置和优化策略**。正确使用 MutationObserver 是构建高性能、可维护的 Web 应用的重要技能。
