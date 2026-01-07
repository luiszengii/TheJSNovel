《第 113 次记录：宿主的规则 —— 从 Node.js 到浏览器世界的觉醒》

## 周末咖啡馆的探索

周六下午，阳光透过咖啡馆的落地窗洒在你的笔记本屏幕上。你点了杯拿铁，舒服地靠在沙发椅上，打开终端查看 npm 包的下载统计：247 次下载，15 个 Star，3 条 Issue 都已关闭。

这是你花了三个月业余时间打磨的 Node.js 数据处理库 `data-transform-kit`。上周五刚发布 1.0.0 版本，测试覆盖率 98%，所有性能基准测试都通过了。你在技术博客上写了篇《纯函数式的数据转换引擎》，评论区已经有十几条讨论，有人说 "elegant"，有人说 "well-designed"。

你轻轻吹了吹咖啡杯里的热气，突然一个念头闪过："这个库能在浏览器里用吗？"

你从来没考虑过这个问题。代码都是纯 JavaScript，没用什么特殊的语法，理论上应该可以吧？你打开浏览器，按下 F12 打开控制台，找到项目主文件 `index.js` 的核心代码，复制，粘贴到控制台，按下回车。

一瞬间，控制台爆出了十几行红色错误信息：

```
Uncaught ReferenceError: __dirname is not defined
    at <anonymous>:3:15
Uncaught ReferenceError: process is not defined
    at <anonymous>:7:9
Uncaught ReferenceError: Buffer is not defined
    at <anonymous>:12:18
Uncaught ReferenceError: require is not defined
    at <anonymous>:1:15
```

你愣了一下，然后笑了："有意思..."

这些变量在 Node.js 里是最基础的全局变量，随处可见。但浏览器说它们"不存在"？你重新审视了一遍代码，确认没有拼写错误。这不是代码的问题，而是环境的问题。

你打开笔记本，新建了一个 Markdown 文件，标题写着：`Node.js vs 浏览器：两个世界的差异`。你决定系统地探索这个问题。

## 两个世界的对话

你泡了杯新咖啡，在浏览器控制台输入：

```javascript
console.log(global);
```

浏览器回应：`Uncaught ReferenceError: global is not defined`

你又试了试：

```javascript
console.log(window);
```

这次，控制台打印出了一个庞大的对象，足足有几百个属性。你点开 `window` 对象，滚动查看它的内容：

```javascript
Window {
  window: Window,
  self: Window,
  document: document,
  name: "",
  location: Location,
  history: History,
  navigator: Navigator,
  screen: Screen,
  frames: Window,
  localStorage: Storage,
  sessionStorage: Storage,
  indexedDB: IDBFactory,
  crypto: Crypto,
  performance: Performance,
  fetch: ƒ fetch(),
  alert: ƒ alert(),
  confirm: ƒ confirm(),
  prompt: ƒ prompt(),
  setTimeout: ƒ setTimeout(),
  setInterval: ƒ setInterval(),
  requestAnimationFrame: ƒ requestAnimationFrame(),
  // ...还有几百个属性
}
```

"原来浏览器的全局对象是 `window`，不是 `global`。" 你在笔记本上记下这一点。

你继续测试。在 Node.js 里，你习惯这样写：

```javascript
// Node.js 环境
const fs = require('fs');
const configPath = __dirname + '/config.json';
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
console.log(config);
```

但在浏览器里，你试着复制这段代码：

```javascript
// 浏览器环境
const fs = require('fs'); // ❌ Uncaught ReferenceError: require is not defined
```

浏览器直接拒绝了。你想了想，Node.js 有文件系统访问能力，浏览器会有吗？你查阅了 MDN，发现浏览器确实可以读取文件，但方式完全不同：

```javascript
// 浏览器环境 - 用户主动选择文件
const input = document.createElement('input');
input.type = 'file';
input.onchange = (e) => {
  const file = e.target.files[0];
  const reader = new FileReader();
  reader.onload = (event) => {
    const config = JSON.parse(event.target.result);
    console.log(config);
  };
  reader.readAsText(file);
};
input.click(); // 弹出文件选择对话框
```

"等等，" 你皱起眉头，"浏览器不能直接读取文件系统？必须让用户手动选择文件？"

你试了试其他方式，比如直接访问本地文件路径：

```javascript
// 浏览器环境
fetch('file:///Users/yourname/config.json')
  .then(res => res.json())
  .catch(err => console.error(err));
```

浏览器控制台立即报错：

```
Access to 'file:///Users/yourname/config.json' from origin 'null' has been blocked
by CORS policy: Cross origin requests are only supported for protocol schemes:
http, https, data, chrome, chrome-extension, chrome-untrusted, https.
```

你恍然大悟。浏览器是一个**严格受限的环境**。它运行在用户的电脑上，如果允许任意网页读取本地文件，那就太危险了。恶意网站可以偷走你的密码文件、浏览历史、个人文档...

"这不是缺陷，" 你在笔记里写道，"这是精心设计的安全边界。"

你打开笔记本，画了个对比图：

**Node.js 宿主环境**：
- 全局对象：`global`、`process`、`Buffer`、`__dirname`、`__filename`
- 模块系统：`require()`、`module.exports`
- 文件系统：`fs.readFile()`、`fs.writeFile()`、直接访问本地文件
- 网络能力：`http.createServer()`、`net.Socket()`、底层网络控制
- 进程控制：`child_process.spawn()`、`process.exit()`
- 安全模型：**完全信任**，可访问一切系统资源

**浏览器宿主环境**：
- 全局对象：`window`、`document`、`navigator`、`location`
- 模块系统：`<script type="module">`、`import`/`export`（ES6+）
- DOM 操作：`document.querySelector()`、`element.appendChild()`
- 用户交互：事件系统、`alert()`、`prompt()`、`confirm()`
- 网络能力：`fetch()`、`XMLHttpRequest()`、`WebSocket()`
- 存储系统：`localStorage`、`sessionStorage`、`IndexedDB`
- 安全模型：**沙箱隔离**、同源策略、严格权限控制

你盯着这张对比图看了好一会儿。"原来 JavaScript 只是语言，环境才是关键。"

## 改造与适配

咖啡馆的下午时光很安静，你决定试试看，能不能把你的库改造成浏览器版本。

你打开 `data-transform-kit` 的源码，第一个问题就出现了：模块加载。

你的库使用 CommonJS 模块系统：

```javascript
// utils.js - Node.js 版本
const validator = require('./validator');
const transformer = require('./transformer');

function processData(data) {
  // ...
}

module.exports = { processData };
```

浏览器不支持 `require`，你需要改成 ES6 模块：

```javascript
// utils.js - 浏览器版本
import { validate } from './validator.js'; // 注意：必须加 .js 后缀
import { transform } from './transformer.js';

export function processData(data) {
  // ...
}
```

然后是文件读取。你的库有个功能是从配置文件读取默认参数：

```javascript
// config-loader.js - Node.js 版本
const fs = require('fs');
const path = require('path');

function loadConfig() {
  const configPath = path.join(__dirname, 'default-config.json');
  const configText = fs.readFileSync(configPath, 'utf8'); // 同步读取
  return JSON.parse(configText);
}

module.exports = loadConfig;
```

在浏览器里，这段代码完全无法工作。你只能这样改：

```javascript
// config-loader.js - 浏览器版本
export async function loadConfig() {
  const response = await fetch('./default-config.json'); // 异步请求
  const configText = await response.text();
  return JSON.parse(configText);
}
```

"等等，" 你意识到一个严重问题，"这不仅仅是换个 API，而是从**同步**变成了**异步**。"

这意味着所有调用 `loadConfig()` 的代码都要改：

```javascript
// 使用方 - Node.js 版本
const config = loadConfig(); // 同步，立即返回结果
processData(data, config);

// 使用方 - 浏览器版本
const config = await loadConfig(); // 异步，必须等待
processData(data, config);
```

而且所有调用链上的函数都必须变成 `async` 函数。这是一次**架构级别的重构**。

你继续检查代码，发现更多无法移植的功能：

```javascript
// 无法在浏览器实现的功能
process.env.NODE_ENV // ❌ 浏览器没有 process 对象
Buffer.from('hello', 'utf8') // ❌ 浏览器没有 Buffer（虽然有替代方案）
__dirname // ❌ 浏览器没有文件系统路径概念
```

但浏览器也提供了很多 Node.js 没有的能力：

```javascript
// 浏览器独有的能力
document.querySelector('.user-input') // ✅ DOM 操作
localStorage.setItem('cache', data) // ✅ 客户端存储
window.location.href // ✅ 当前 URL
navigator.geolocation.getCurrentPosition() // ✅ 地理位置
```

傍晚 5 点，咖啡馆开始播放爵士乐。你站起来伸了个懒腰，看着笔记本屏幕上的代码。经过 3 小时的改造，你写出了一个同时支持 Node.js 和浏览器的版本：

```javascript
// index.js - 通用版本
// 环境检测
const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';
const isNode = typeof process !== 'undefined' &&
               process.versions != null &&
               process.versions.node != null;

// 根据环境选择不同的实现
let loadConfig;
if (isBrowser) {
  loadConfig = async () => {
    const res = await fetch('./config.json');
    return res.json();
  };
} else if (isNode) {
  const fs = require('fs');
  const path = require('path');
  loadConfig = () => {
    const configPath = path.join(__dirname, 'config.json');
    return JSON.parse(fs.readFileSync(configPath, 'utf8'));
  };
}

export async function transform(data, options = {}) {
  const config = await loadConfig();
  // ...转换逻辑
  return result;
}
```

你关上笔记本，对这次周末探索很满意。虽然没有做出一个完美的跨平台库，但你理解了 JavaScript 世界的一个核心真相：

**JavaScript 只是语言，环境才是舞台。同样的演员，在不同的舞台上，能做的事情完全不同。**

## 宿主环境法则

**规则 1: JavaScript 引擎不等于运行环境**

JavaScript 语言本身只定义了核心语法：

- 变量、函数、对象、类
- Promise、async/await、Generator
- Array、Map、Set 等内置对象
- 运算符、控制流、模块语法

但这些只是"语言"，不是"环境"。JavaScript 必须依附在**宿主环境**（Host Environment）中才能运行。宿主环境提供：

1. **全局对象**：Node.js 的 `global`、浏览器的 `window`、Web Workers 的 `self`
2. **API 集合**：文件系统、网络、DOM、定时器等
3. **模块系统**：如何加载和组织代码
4. **安全策略**：能做什么、不能做什么

常见的宿主环境：

| 环境 | 全局对象 | 主要能力 | 典型应用 |
|------|---------|---------|---------|
| **浏览器** | `window` | DOM 操作、网络请求、本地存储 | 网页应用 |
| **Node.js** | `global` | 文件系统、进程控制、网络服务器 | 后端服务 |
| **Deno** | `globalThis` | 安全沙箱、TypeScript 支持、Web 标准 API | 现代运行时 |
| **Web Workers** | `self` | 后台计算、多线程 | 性能优化 |
| **React Native** | `global` | 原生 UI 组件、设备 API | 移动应用 |

**规则 2: 浏览器的全局对象是 `window`**

在浏览器中，所有全局变量和函数都是 `window` 对象的属性：

```javascript
// 这些都是等价的
var globalVar = 'test';
window.globalVar = 'test';

function globalFunc() {}
window.globalFunc = function() {};

console.log(window.globalVar); // "test"
console.log(window.globalFunc); // function
```

但有一个重要的例外：使用 `let`/`const` 声明的变量**不会**成为 `window` 的属性（这是 ES6 的改进，避免污染全局对象）：

```javascript
let modernVar = 'test';
const modernConst = 'constant';

console.log(window.modernVar); // undefined
console.log(window.modernConst); // undefined
```

`window` 对象的特殊属性：

```javascript
window.window === window // true，循环引用
window.self === window // true，指向自己
window.top // 顶层窗口（iframe 中有用）
window.parent // 父窗口（iframe 中有用）
```

**规则 3: 浏览器的零信任沙箱**

浏览器环境是**零信任沙箱**（Zero-Trust Sandbox），默认禁止访问：

- ❌ **本地文件系统**（除非用户主动通过 `<input type="file">` 选择）
- ❌ **跨域网络资源**（除非服务器明确允许 CORS）
- ❌ **系统级 API**（进程、硬件直接访问）
- ❌ **其他标签页的内容**（除非同源且通过 `window.opener` 或 `postMessage` 通信）

这些限制**无法绕过**，任何尝试都会被浏览器安全机制阻止。

安全边界的设计目标：

1. **保护用户隐私**：网页不能偷看你的文件、浏览历史、密码
2. **防止恶意攻击**：网页不能执行系统命令、安装恶意软件
3. **隔离不同来源的代码**：不同网站的代码互不干扰

**规则 4: 浏览器专属 API 的三层结构**

浏览器提供的 API 可以分为三层：

**① BOM (Browser Object Model) - 浏览器对象模型**：

```javascript
window.location.href // 当前 URL
window.location.reload() // 刷新页面
window.history.back() // 后退
window.history.pushState() // 修改 URL（不刷新）
window.navigator.userAgent // 浏览器信息
window.navigator.geolocation.getCurrentPosition() // 地理位置
window.screen.width // 屏幕宽度
window.alert('提示') // 弹窗
window.confirm('确认？') // 确认框
window.prompt('输入') // 输入框
```

**② DOM (Document Object Model) - 文档对象模型**：

```javascript
document.querySelector('.class') // 查询元素
document.createElement('div') // 创建元素
element.appendChild(child) // 插入子元素
element.addEventListener('click', handler) // 添加事件监听器
element.classList.add('active') // 添加 CSS 类
element.style.color = 'red' // 修改样式
```

**③ Web APIs - 现代 Web 能力**：

```javascript
fetch('https://api.example.com/data') // 网络请求
localStorage.setItem('key', 'value') // 持久存储
sessionStorage.setItem('key', 'value') // 会话存储
indexedDB.open('myDatabase') // 结构化数据库
new WebSocket('wss://server.com') // WebSocket 连接
new Worker('worker.js') // Web Worker 多线程
navigator.serviceWorker.register() // Service Worker 离线支持
new Notification('提示') // 桌面通知
```

这些 API 都**不是 JavaScript 语言规范的一部分**，而是浏览器宿主环境额外提供的能力。在 Node.js 中，这些 API 都不存在。

**规则 5: 环境检测是跨平台代码的必需品**

如果代码需要同时在 Node.js 和浏览器中运行，必须进行**环境检测**：

```javascript
// 检测是否在浏览器环境
const isBrowser = typeof window !== 'undefined' &&
                  typeof document !== 'undefined';

// 检测是否在 Node.js 环境
const isNode = typeof process !== 'undefined' &&
               process.versions != null &&
               process.versions.node != null;

// 检测是否在 Web Worker 环境
const isWebWorker = typeof self !== 'undefined' &&
                    typeof WorkerGlobalScope !== 'undefined';

// ES2020 标准：所有环境都有 globalThis
const globalObject = globalThis; // 浏览器中是 window，Node.js 中是 global
```

根据环境选择不同的实现：

```javascript
// 跨平台的配置加载
async function loadConfig() {
  if (isBrowser) {
    const res = await fetch('/config.json');
    return res.json();
  } else if (isNode) {
    const fs = require('fs').promises;
    const text = await fs.readFile('./config.json', 'utf8');
    return JSON.parse(text);
  }
}
```

**规则 6: 浏览器的异步优先设计**

浏览器中几乎所有 I/O 操作都是**异步**的：

```javascript
// ✅ 浏览器中的异步操作
fetch('/api/data') // 网络请求
indexedDB.open() // 数据库打开
new FileReader().readAsText(file) // 文件读取
navigator.geolocation.getCurrentPosition() // 地理位置
```

这是因为浏览器必须保持 **UI 线程不被阻塞**，否则网页会"卡死"，用户无法滚动、点击、输入。

Node.js 则同时提供同步和异步两种选择：

```javascript
// Node.js 可以选择同步
const text = fs.readFileSync('./file.txt', 'utf8'); // 阻塞执行

// 也可以选择异步
const text = await fs.promises.readFile('./file.txt', 'utf8'); // 非阻塞
```

但在浏览器中，没有"同步 I/O"的选项。所有涉及外部资源的操作都必须使用 Promise、async/await 或回调函数。

---

**记录者注**：

宿主环境是 JavaScript 世界的"物理规则"。同样的代码，在不同宿主中的行为可能完全不同。

浏览器宿主是一个精心设计的牢笼 —— 它给了你操作网页的无限可能，DOM 树可以任意修改，事件可以自由监听，网络请求可以随意发送。但它绝不让你触碰用户系统的安全边界。你不能读取本地文件，不能执行系统命令，不能访问其他网站的数据。

这不是限制，而是保护。理解宿主环境的边界，是从"写代码"到"写可靠代码"的关键一步。
