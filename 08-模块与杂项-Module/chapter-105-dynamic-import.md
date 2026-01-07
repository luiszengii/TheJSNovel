《第 105 次记录: 首屏白屏灾难 —— 动态导入的性能救赎》

---

## 首屏加载的性能噩梦

周二上午九点, 你盯着 Lighthouse 报告, 额头渗出了冷汗。

这是昨天刚上线的新版管理后台。产品经理对新设计赞不绝口, 但今天早上, 运营部门的投诉电话就打爆了: "页面加载太慢了! 白屏时间超过 8 秒, 用户都在抱怨!"

你打开 DevTools 的 Network 面板, 看到了令人震惊的数字:

```
main.js: 3.2MB (gzipped: 892KB)
Load time: 7.8s (3G network)
```

"3.2MB 的 JavaScript?" 你难以置信, "怎么会这么大?"

你打开 webpack-bundle-analyzer 报告, 看到了问题的根源——所有的功能模块都被打包到了一个文件里:

```
main.js (3.2MB):
├── echarts.js (756KB)           - 图表库, 只在报表页面用
├── monaco-editor.js (1.1MB)     - 代码编辑器, 只在配置页面用
├── pdf-lib.js (384KB)           - PDF 生成, 只在导出功能用
├── xlsx.js (512KB)              - Excel 处理, 只在导入功能用
└── core.js (448KB)              - 核心业务代码
```

"这些库根本不是首屏需要的, " 你喃喃自语, "为什么要在启动时全部加载?"

你查看代码, 看到了问题所在:

```javascript
// main.js
import * as echarts from 'echarts';
import * as monaco from 'monaco-editor';
import { PDFDocument } from 'pdf-lib';
import * as XLSX from 'xlsx';

// 路由配置
const routes = [
    { path: '/dashboard', component: Dashboard },
    { path: '/reports', component: Reports },      // 用到 echarts
    { path: '/config', component: ConfigEditor },  // 用到 monaco
    { path: '/export', component: ExportPage },    // 用到 pdf-lib
    { path: '/import', component: ImportPage }     // 用到 XLSX
];
```

"所有的 import 都是静态的, " 你意识到问题的严重性, "它们会在模块顶部立即执行, 即使用户可能永远不会访问那些页面..."

产品经理走了过来: "性能报告出来了吗? 什么时候能优化完?"

你看着报告上的数字, 知道必须找到解决方案。

---

## 动态 import() 的发现

上午十点, 你开始搜索 "JavaScript lazy loading"。

在 MDN 文档上, 你看到了一个从未注意过的语法: **`import()` 函数**。

"等等, " 你盯着示例代码, "import 还能当函数用?"

文档解释:

> **动态导入 (Dynamic Import)**: `import()` 是一个类似函数的表达式, 可以在运行时按需加载模块。它返回一个 Promise, 在模块加载完成后 resolve。

你立刻测试:

```javascript
// 传统的静态导入
import * as echarts from 'echarts';  // 立即加载

// 动态导入
import('echarts').then(function(echarts) {
    console.log('echarts 加载完成', echarts);
});
```

"这样就可以延迟加载了?" 你继续测试:

```javascript
// 按钮点击时才加载
document.querySelector('#show-chart').addEventListener('click', function() {
    console.log('开始加载 echarts...');

    import('echarts').then(function(echarts) {
        console.log('echarts 加载完成');
        // 初始化图表
        const chart = echarts.init(document.querySelector('#chart'));
        chart.setOption({ /* ... */ });
    });
});
```

你打开页面, 查看 Network 面板——初始加载时, echarts 并没有被加载! 只有当你点击按钮时, 才看到网络请求:

```
Request: echarts.js (756KB)
Status: 200 OK
Time: 1.2s
```

"太神奇了!" 你兴奋地说, "**`import()` 可以让模块在需要时才加载, 而不是启动时全部加载**!"

---

## 路由级别的代码分割

上午十一点, 你开始重构路由系统。

"既然可以动态加载模块, " 你想, "那路由组件也可以按需加载。"

你修改了路由配置:

```javascript
// ❌ 旧代码: 静态导入所有组件
import Dashboard from './pages/Dashboard.js';
import Reports from './pages/Reports.js';
import ConfigEditor from './pages/ConfigEditor.js';

const routes = [
    { path: '/dashboard', component: Dashboard },
    { path: '/reports', component: Reports },
    { path: '/config', component: ConfigEditor }
];

// ✅ 新代码: 动态导入
const routes = [
    {
        path: '/dashboard',
        component: function() {
            return import('./pages/Dashboard.js');
        }
    },
    {
        path: '/reports',
        component: function() {
            return import('./pages/Reports.js');
        }
    },
    {
        path: '/config',
        component: function() {
            return import('./pages/ConfigEditor.js');
        }
    }
];
```

你实现了路由加载逻辑:

```javascript
async function loadRoute(path) {
    // 查找路由
    const route = routes.find(r => r.path === path);

    if (!route) {
        console.error('路由不存在:', path);
        return;
    }

    try {
        // 显示 loading
        showLoading();

        // 动态加载组件
        const module = await route.component();

        // module.default 是默认导出的组件
        const Component = module.default;

        // 渲染组件
        renderComponent(Component);

        // 隐藏 loading
        hideLoading();
    } catch (error) {
        console.error('加载路由失败:', error);
        showError('页面加载失败, 请刷新重试');
    }
}

// 用户导航时加载
window.addEventListener('hashchange', function() {
    const path = location.hash.slice(1) || '/dashboard';
    loadRoute(path);
});
```

你测试新版本, 打开 Network 面板——首屏只加载了 core.js (448KB), 其他组件按需加载:

```
首屏加载:
main.js: 448KB (仅核心代码)
Load time: 2.1s ✓

用户访问 /reports:
Reports.js: 892KB (包含 echarts)
Load time: 1.3s ✓

用户访问 /config:
ConfigEditor.js: 1.2MB (包含 monaco-editor)
Load time: 1.5s ✓
```

"加载时间从 7.8 秒降到了 2.1 秒!" 你兴奋地说, "而且用户只加载他们实际访问的页面!"

---

## 动态导入的返回值

中午十二点, 你开始深入研究 `import()` 的行为。

"既然 `import()` 返回 Promise, " 你想, "那 Promise 的值是什么?"

你测试了不同的导出方式:

```javascript
// test-module.js
export const a = 1;
export function test() {
    console.log('test');
}
export default class User {
    constructor(name) {
        this.name = name;
    }
}

// main.js
import('./test-module.js').then(function(module) {
    console.log(module);  // 看看返回了什么
});
```

控制台输出:

```javascript
{
    a: 1,
    test: ƒ test(),
    default: class User { /* ... */ },
    __esModule: true
}
```

"原来如此, " 你恍然大悟, "**`import()` 返回的是模块命名空间对象, 包含所有导出内容**!"

你总结了访问方式:

```javascript
import('./test-module.js').then(function(module) {
    // 访问具名导出
    console.log(module.a);  // 1
    module.test();  // 'test'

    // 访问默认导出
    const User = module.default;
    const user = new User('Alice');
});

// 或者用解构
import('./test-module.js').then(function({ a, test, default: User }) {
    console.log(a);  // 1
    test();  // 'test'
    const user = new User('Alice');
});

// 或者用 async/await (最清晰)
async function loadModule() {
    const { a, test, default: User } = await import('./test-module.js');

    console.log(a);
    test();
    const user = new User('Alice');
}
```

"等等, " 你注意到一个问题, "为什么默认导出要用 `default: User` 重命名?"

你查阅文档, 发现 `default` 是 JavaScript 的保留字, 不能直接用作变量名:

```javascript
// ❌ 错误: default 是保留字
const { default } = await import('./module.js');

// ✅ 正确: 必须重命名
const { default: Module } = await import('./module.js');
```

---

## 条件加载与 Polyfill 注入

下午两点, 你遇到了一个浏览器兼容性问题。

项目需要使用 Intl.RelativeTimeFormat API, 但它在旧浏览器中不支持。你需要在不支持的浏览器中动态加载 polyfill。

"这正是动态导入的用武之地, " 你想。

你写下了条件加载逻辑:

```javascript
async function ensureRelativeTimeFormat() {
    // 检测浏览器是否支持
    if (typeof Intl.RelativeTimeFormat === 'undefined') {
        console.log('浏览器不支持 Intl.RelativeTimeFormat, 加载 polyfill...');

        // 动态加载 polyfill
        await import('@formatjs/intl-relativetimeformat/polyfill');
        await import('@formatjs/intl-relativetimeformat/locale-data/zh');

        console.log('Polyfill 加载完成');
    } else {
        console.log('浏览器原生支持 Intl.RelativeTimeFormat');
    }
}

// 使用
async function formatRelativeTime(value, unit) {
    // 确保 API 可用
    await ensureRelativeTimeFormat();

    // 使用 API
    const rtf = new Intl.RelativeTimeFormat('zh-CN', { numeric: 'auto' });
    return rtf.format(value, unit);
}

// 测试
formatRelativeTime(-1, 'day').then(function(result) {
    console.log(result);  // '昨天'
});
```

你在不同浏览器中测试:

```
现代浏览器 (Chrome 110):
✓ 浏览器原生支持 Intl.RelativeTimeFormat
✓ 无需加载 polyfill
✓ 首屏加载: 0KB polyfill

旧浏览器 (Chrome 60):
✓ 浏览器不支持 Intl.RelativeTimeFormat, 加载 polyfill...
✓ Polyfill 加载完成
✓ 首屏加载: 0KB, 运行时加载: 124KB polyfill
```

"完美!" 你说, "**动态导入让我们只在需要时加载 polyfill, 现代浏览器完全不受影响**。"

你又想到了另一个应用场景——根据用户语言加载翻译文件:

```javascript
async function loadTranslations(language) {
    console.log('加载', language, '翻译...');

    try {
        // 动态加载对应语言的翻译文件
        const translations = await import(`./i18n/${language}.js`);

        return translations.default;
    } catch (error) {
        console.warn('翻译文件不存在, 回退到英文:', language);

        // 回退到英文
        const fallback = await import('./i18n/en.js');
        return fallback.default;
    }
}

// 用户切换语言时加载
async function changeLanguage(lang) {
    const translations = await loadTranslations(lang);

    // 应用翻译
    applyTranslations(translations);
}

// 测试
changeLanguage('zh-CN');  // 加载 zh-CN.js
changeLanguage('ja-JP');  // 加载 ja-JP.js
```

---

## 动态导入的缓存机制

下午三点, 你注意到一个有趣的现象。

你多次动态导入同一个模块:

```javascript
// 第一次导入
console.log('第一次导入...');
const module1 = await import('./test.js');
console.log('第一次完成');

// 第二次导入
console.log('第二次导入...');
const module2 = await import('./test.js');
console.log('第二次完成');

// 比较两个模块
console.log(module1 === module2);  // true - 是同一个对象
```

你打开 Network 面板, 发现只有第一次导入时才发送了网络请求, 第二次直接从缓存返回。

"等等, " 你想, "动态导入也有模块缓存机制?"

你查阅规范, 确认了这个行为:

> **模块缓存**: 无论是静态导入还是动态导入, 同一个模块只会被执行一次。后续导入会返回缓存的模块实例。

你测试了模块执行次数:

```javascript
// test.js
console.log('test.js 模块执行');
export const value = Math.random();

// main.js
const module1 = await import('./test.js');
console.log('module1.value:', module1.value);

const module2 = await import('./test.js');
console.log('module2.value:', module2.value);

// 输出:
// test.js 模块执行  ← 只执行一次
// module1.value: 0.123456
// module2.value: 0.123456  ← 相同的值
```

"所以动态导入和静态导入共享模块缓存, " 你总结, "同一个模块只会执行一次, 所有导入共享同一个实例。"

你又测试了混合使用静态和动态导入:

```javascript
// main.js
import { value as staticValue } from './test.js';  // 静态导入

console.log('静态导入 value:', staticValue);

// 稍后动态导入
const module = await import('./test.js');
console.log('动态导入 value:', module.value);

console.log(staticValue === module.value);  // true - 共享同一个模块
```

"静态导入和动态导入使用同一个模块缓存, " 你说, "这保证了模块的单例性。"

---

## 动态导入的错误处理

下午四点, 你开始处理加载失败的场景。

"如果模块加载失败怎么办?" 你想, "网络错误、模块不存在、语法错误..."

你测试了错误场景:

```javascript
// 场景 1: 模块不存在
try {
    await import('./non-existent.js');
} catch (error) {
    console.error('加载失败:', error);
    // TypeError: Failed to fetch dynamically imported module
}

// 场景 2: 网络错误 (模拟离线)
try {
    await import('https://cdn.example.com/library.js');
} catch (error) {
    console.error('网络错误:', error);
    // TypeError: Failed to fetch
}

// 场景 3: 模块语法错误
// buggy-module.js
export const a = ;  // 语法错误

try {
    await import('./buggy-module.js');
} catch (error) {
    console.error('语法错误:', error);
    // SyntaxError: Unexpected token
}
```

"所有加载失败都会导致 Promise reject, " 你说, "必须用 try...catch 或 .catch() 处理。"

你实现了一个带重试机制的加载器:

```javascript
async function importWithRetry(modulePath, maxRetries = 3) {
    let lastError;

    for (let i = 0; i < maxRetries; i++) {
        try {
            console.log(`尝试加载 ${modulePath} (第 ${i + 1} 次)...`);

            const module = await import(modulePath);

            console.log('加载成功');
            return module;
        } catch (error) {
            console.warn(`加载失败 (第 ${i + 1} 次):`, error.message);

            lastError = error;

            // 等待一段时间后重试
            await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        }
    }

    // 所有重试都失败
    throw new Error(`加载 ${modulePath} 失败 (已重试 ${maxRetries} 次): ${lastError.message}`);
}

// 使用
try {
    const echarts = await importWithRetry('./echarts.js');
    console.log('echarts 加载成功');
} catch (error) {
    console.error('最终加载失败:', error);
    showError('图表库加载失败, 请刷新页面重试');
}
```

你又实现了一个带降级方案的加载器:

```javascript
async function importWithFallback(primaryPath, fallbackPath) {
    try {
        // 尝试加载主要模块
        console.log('加载主要模块:', primaryPath);
        return await import(primaryPath);
    } catch (primaryError) {
        console.warn('主要模块加载失败, 尝试降级方案:', primaryError.message);

        try {
            // 尝试加载降级模块
            console.log('加载降级模块:', fallbackPath);
            return await import(fallbackPath);
        } catch (fallbackError) {
            console.error('降级方案也失败了:', fallbackError.message);
            throw new Error('所有加载方案都失败');
        }
    }
}

// 使用: 优先加载 CDN, 失败则加载本地副本
const echarts = await importWithFallback(
    'https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js',
    './vendor/echarts.min.js'
);
```

---

## 动态导入的路径限制

下午五点, 你遇到了一个奇怪的错误。

你尝试根据用户输入动态加载插件:

```javascript
// 用户输入插件名
const pluginName = prompt('输入插件名:');

// 尝试加载
try {
    const plugin = await import(`./plugins/${pluginName}.js`);
    console.log('插件加载成功:', plugin);
} catch (error) {
    console.error('插件加载失败:', error);
}
```

你输入 "chart", 期望加载 `./plugins/chart.js`, 但浏览器报错:

```
Error: Cannot find module './plugins/chart.js'
```

"明明文件存在, 为什么找不到?" 你困惑。

你查阅文档, 发现了一个重要限制:

> **路径限制**: `import()` 的路径参数可以是动态表达式, 但构建工具 (如 webpack) 需要在编译时分析可能的路径。完全动态的路径可能无法被正确处理。

你检查 webpack 的编译输出, 发现它生成了多个 chunk 文件:

```
dist/
├── main.js
├── plugins-chart.js
├── plugins-table.js
├── plugins-form.js
└── ...
```

"原来 webpack 在编译时就把所有 `./plugins/*.js` 文件提取出来了, " 你说, "但如果路径是完全动态的变量, webpack 无法静态分析。"

你修改了代码, 使用更明确的路径模式:

```javascript
// ❌ 错误: 完全动态, webpack 无法分析
const module = await import(userInput);

// ✅ 正确: 路径模式明确, webpack 可以分析
const module = await import(`./plugins/${pluginName}.js`);

// ✅ 更好: 白名单验证
const allowedPlugins = ['chart', 'table', 'form'];

if (allowedPlugins.includes(pluginName)) {
    const module = await import(`./plugins/${pluginName}.js`);
} else {
    throw new Error('插件不存在或不允许加载');
}
```

---

## 你的动态导入笔记本

晚上八点, 你整理了今天的收获。

你在笔记本上写下标题: "动态导入 —— 按需加载的性能救星"

### 核心洞察 #1: import() 函数语法

你写道:

"动态导入使用 `import()` 函数, 返回 Promise:

```javascript
// 静态导入 (编译时确定)
import * as echarts from 'echarts';

// 动态导入 (运行时加载)
import('echarts').then(function(echarts) {
    // echarts 加载完成
});

// 使用 async/await
async function loadChart() {
    const echarts = await import('echarts');
    // 使用 echarts
}
```

核心特性:
- `import()` 是表达式, 可以在任何地方使用
- 返回 Promise, resolve 值是模块命名空间对象
- 可以在条件语句、函数内部使用
- 路径可以是动态表达式 (有限制)"

### 核心洞察 #2: 模块命名空间对象

"动态导入返回的是完整的模块对象:

```javascript
// module.js
export const a = 1;
export function test() {}
export default class User {}

// 动态导入
const module = await import('./module.js');

// 访问具名导出
console.log(module.a);  // 1
module.test();

// 访问默认导出
const User = module.default;

// 或者用解构
const { a, test, default: User } = await import('./module.js');
```

关键规则:
- 返回值包含所有导出内容
- 默认导出挂载在 `default` 属性
- 解构时必须重命名 `default` (保留字)"

### 核心洞察 #3: 代码分割与懒加载

"动态导入实现路由级别代码分割:

```javascript
const routes = [
    {
        path: '/reports',
        component: () => import('./pages/Reports.js')  // 懒加载
    },
    {
        path: '/config',
        component: () => import('./pages/ConfigEditor.js')
    }
];

// 路由加载
async function loadRoute(path) {
    const route = routes.find(r => r.path === path);
    const module = await route.component();
    const Component = module.default;
    renderComponent(Component);
}
```

性能提升:
- 首屏只加载必要代码
- 按需加载其他页面
- 减少初始 bundle 大小
- 提升首屏加载速度"

### 核心洞察 #4: 条件加载与 Polyfill

"根据条件动态加载模块:

```javascript
// Polyfill 注入
async function ensureAPI() {
    if (typeof Intl.RelativeTimeFormat === 'undefined') {
        // 只在需要时加载 polyfill
        await import('@formatjs/intl-relativetimeformat/polyfill');
    }
}

// 语言文件按需加载
async function loadTranslations(lang) {
    const translations = await import(`./i18n/${lang}.js`);
    return translations.default;
}

// 根据设备类型加载不同模块
async function loadRenderer() {
    if (isMobile()) {
        return await import('./renderers/mobile.js');
    } else {
        return await import('./renderers/desktop.js');
    }
}
```

优势:
- 减少不必要的代码加载
- 提升性能和用户体验
- 支持渐进增强"

你合上笔记本, 关掉电脑。

"明天要学习 Proxy 了, " 你想, "今天终于掌握了动态导入——它是性能优化的关键工具。通过 `import()` 函数, 我们可以在运行时按需加载模块, 而不是在启动时全部加载。这大幅减少了首屏加载时间, 提升了用户体验。理解动态导入, 才能构建高性能的现代 Web 应用。"

---

## 知识总结

**规则 1: 动态导入的基本语法**

`import()` 是一个类似函数的表达式, 可以在运行时加载模块:

```javascript
// 静态导入 (传统方式, 编译时确定)
import { a, b } from './module.js';  // 顶层, 不能条件化

// 动态导入 (运行时加载)
import('./module.js').then(function(module) {
    console.log(module.a);
    console.log(module.b);
});

// 使用 async/await
async function loadModule() {
    const module = await import('./module.js');
    console.log(module.a);
}

// 在条件语句中使用
if (needFeature) {
    const feature = await import('./feature.js');
    feature.init();
}

// 在函数内部使用
function onClick() {
    import('./modal.js').then(function(modal) {
        modal.show();
    });
}
```

核心特性:
- `import()` 返回 Promise, resolve 值是模块命名空间对象
- 可以在任何地方使用, 不限于模块顶层
- 支持条件加载和延迟加载
- 路径可以是动态表达式 (有限制)

---

**规则 2: 模块命名空间对象**

动态导入返回的是完整的模块对象, 包含所有导出内容:

```javascript
// module.js
export const a = 1;
export function test() {
    console.log('test');
}
export default class User {
    constructor(name) {
        this.name = name;
    }
}

// 动态导入
const module = await import('./module.js');

// 访问具名导出
console.log(module.a);  // 1
module.test();  // 'test'

// 访问默认导出 (挂载在 default 属性)
const User = module.default;
const user = new User('Alice');

// 解构导入 (推荐)
const { a, test, default: User } = await import('./module.js');
```

关键规则:
- 返回值是对象, 包含所有导出 (具名 + 默认)
- 默认导出挂载在 `default` 属性
- 解构时必须重命名 `default` (因为是保留字)
- 与静态导入的 `import * as module` 返回值相同

---

**规则 3: 代码分割 (Code Splitting)**

动态导入最大的应用场景是代码分割, 减少初始 bundle 大小:

```javascript
// ❌ 问题: 所有页面组件在启动时全部加载
import Dashboard from './pages/Dashboard.js';
import Reports from './pages/Reports.js';
import ConfigEditor from './pages/ConfigEditor.js';

const routes = [
    { path: '/dashboard', component: Dashboard },
    { path: '/reports', component: Reports },
    { path: '/config', component: ConfigEditor }
];

// ✅ 解决: 路由级别代码分割
const routes = [
    {
        path: '/dashboard',
        component: () => import('./pages/Dashboard.js')
    },
    {
        path: '/reports',
        component: () => import('./pages/Reports.js')
    },
    {
        path: '/config',
        component: () => import('./pages/ConfigEditor.js')
    }
];

// 路由加载函数
async function loadRoute(path) {
    const route = routes.find(r => r.path === path);

    if (!route) {
        throw new Error('路由不存在');
    }

    // 动态加载组件
    const module = await route.component();

    // 默认导出是组件
    const Component = module.default;

    // 渲染组件
    renderComponent(Component);
}
```

性能提升:
- **首屏加载**: 只加载核心代码, 其他页面延迟加载
- **按需加载**: 用户访问时才加载对应页面
- **Bundle 优化**: webpack 自动拆分成多个 chunk 文件
- **用户体验**: 减少白屏时间, 提升首屏速度

---

**规则 4: 条件加载与 Polyfill 注入**

根据条件动态加载模块, 避免不必要的代码:

```javascript
// 场景 1: Polyfill 按需加载
async function ensureRelativeTimeFormat() {
    // 检测浏览器支持
    if (typeof Intl.RelativeTimeFormat === 'undefined') {
        console.log('加载 polyfill...');

        // 动态加载 polyfill
        await import('@formatjs/intl-relativetimeformat/polyfill');
        await import('@formatjs/intl-relativetimeformat/locale-data/zh');

        console.log('Polyfill 加载完成');
    }
}

// 场景 2: 语言文件按需加载
async function loadTranslations(lang) {
    try {
        const translations = await import(`./i18n/${lang}.js`);
        return translations.default;
    } catch (error) {
        // 回退到英文
        const fallback = await import('./i18n/en.js');
        return fallback.default;
    }
}

// 场景 3: 根据设备类型加载不同实现
async function loadRenderer() {
    if (isMobile()) {
        return await import('./renderers/mobile.js');
    } else {
        return await import('./renderers/desktop.js');
    }
}

// 场景 4: 功能开关
if (enableAdvancedFeatures) {
    const advanced = await import('./features/advanced.js');
    advanced.init();
}
```

优势:
- 现代浏览器不加载 polyfill, 旧浏览器按需加载
- 多语言应用只加载当前语言文件
- 根据环境加载不同实现
- 支持渐进增强和降级方案

---

**规则 5: 模块缓存机制**

动态导入和静态导入共享模块缓存, 同一个模块只执行一次:

```javascript
// test.js
console.log('test.js 模块执行');
export const value = Math.random();

// main.js
// 静态导入
import { value as staticValue } from './test.js';
console.log('静态导入:', staticValue);

// 动态导入 (第一次)
const module1 = await import('./test.js');
console.log('动态导入 1:', module1.value);

// 动态导入 (第二次)
const module2 = await import('./test.js');
console.log('动态导入 2:', module2.value);

// 输出:
// test.js 模块执行  ← 只执行一次
// 静态导入: 0.123456
// 动态导入 1: 0.123456  ← 相同的值
// 动态导入 2: 0.123456  ← 相同的值

// 验证是同一个对象
console.log(staticValue === module1.value);  // true
console.log(module1 === module2);  // true
```

缓存规则:
- 无论静态导入还是动态导入, 同一个模块只执行一次
- 后续导入返回缓存的模块实例
- 所有导入共享同一个模块命名空间对象
- 保证模块的单例性

---

**规则 6: 错误处理**

动态导入失败会导致 Promise reject, 必须处理错误:

```javascript
// 场景 1: 模块不存在
try {
    await import('./non-existent.js');
} catch (error) {
    console.error('模块不存在:', error);
    // TypeError: Failed to fetch dynamically imported module
}

// 场景 2: 网络错误
try {
    await import('https://cdn.example.com/library.js');
} catch (error) {
    console.error('网络错误:', error);
    // TypeError: Failed to fetch
}

// 场景 3: 模块语法错误
try {
    await import('./buggy-module.js');
} catch (error) {
    console.error('语法错误:', error);
    // SyntaxError: Unexpected token
}
```

重试机制:

```javascript
async function importWithRetry(modulePath, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await import(modulePath);
        } catch (error) {
            if (i === maxRetries - 1) throw error;

            // 等待后重试
            await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        }
    }
}
```

降级方案:

```javascript
async function importWithFallback(primaryPath, fallbackPath) {
    try {
        return await import(primaryPath);
    } catch (primaryError) {
        console.warn('主要模块失败, 尝试降级:', primaryError);
        return await import(fallbackPath);
    }
}

// 使用: CDN 失败则加载本地副本
const echarts = await importWithFallback(
    'https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js',
    './vendor/echarts.min.js'
);
```

---

**规则 7: 路径限制与安全性**

动态导入的路径可以是表达式, 但有限制:

```javascript
// ✅ 正确: 路径模式明确
const pluginName = 'chart';
const plugin = await import(`./plugins/${pluginName}.js`);

// ❌ 问题: 完全动态路径, 构建工具无法静态分析
const userPath = prompt('输入路径:');
const module = await import(userPath);  // webpack 无法处理

// ✅ 改进: 白名单验证
const allowedPlugins = ['chart', 'table', 'form'];

if (allowedPlugins.includes(pluginName)) {
    const plugin = await import(`./plugins/${pluginName}.js`);
} else {
    throw new Error('插件不存在或不允许加载');
}
```

路径规则:
- 路径可以包含动态变量, 但必须有明确的路径模式
- 构建工具 (如 webpack) 需要在编译时分析可能的路径
- 完全动态的路径 (如用户输入) 可能无法正确处理
- 必须进行白名单验证, 防止路径注入攻击

安全考虑:
- **路径遍历攻击**: 验证路径, 防止 `../../` 访问敏感文件
- **代码注入**: 不要直接使用用户输入作为路径
- **白名单**: 只允许加载已知的、安全的模块
- **CSP**: 配置 Content Security Policy 限制动态加载来源

---

**规则 8: 动态导入的最佳实践**

**推荐做法**:

```javascript
// ✅ 路由级别代码分割
const routes = [
    { path: '/page', component: () => import('./pages/Page.js') }
];

// ✅ 组件懒加载
function showModal() {
    import('./components/Modal.js').then(({ default: Modal }) => {
        new Modal().show();
    });
}

// ✅ Polyfill 按需加载
if (!('IntersectionObserver' in window)) {
    await import('intersection-observer');
}

// ✅ 错误处理和降级
try {
    const module = await import('./module.js');
} catch (error) {
    console.error('加载失败:', error);
    showError('功能暂时不可用, 请刷新重试');
}
```

**避免的做法**:

```javascript
// ❌ 避免: 过度拆分导致请求过多
// 每个小工具函数都动态加载
const { add } = await import('./utils/add.js');
const { multiply } = await import('./utils/multiply.js');

// ✅ 改进: 合理聚合
const utils = await import('./utils/index.js');
utils.add();
utils.multiply();

// ❌ 避免: 在循环中动态导入
for (const plugin of plugins) {
    await import(`./plugins/${plugin}.js`);  // 串行加载, 慢
}

// ✅ 改进: 并行加载
await Promise.all(
    plugins.map(plugin => import(`./plugins/${plugin}.js`))
);

// ❌ 避免: 缺少错误处理
const module = await import('./module.js');  // 可能抛出异常

// ✅ 改进: 添加错误处理
try {
    const module = await import('./module.js');
} catch (error) {
    // 处理错误
}
```

---

**事故档案编号**: MODULE-2024-1905
**影响范围**: 动态导入, 代码分割, 懒加载, 性能优化
**根本原因**: 静态导入所有模块导致首屏加载时间过长
**修复成本**: 低 (改用动态导入即可大幅提升性能)

这是 JavaScript 世界第 105 次被记录的模块系统事故。动态导入使用 `import()` 函数在运行时按需加载模块, 返回 Promise, resolve 值是模块命名空间对象。最大应用场景是代码分割, 将大型应用拆分成多个小 chunk, 按需加载, 大幅减少首屏加载时间。动态导入和静态导入共享模块缓存, 同一个模块只执行一次。路径可以是动态表达式, 但必须有明确的路径模式供构建工具分析。动态导入失败会导致 Promise reject, 必须处理错误。理解动态导入是构建高性能现代 Web 应用的关键技术。

---
