《第 129 次记录：按键的秘密 —— 从物理按键到字符输入的转换》

## 快捷键冲突事故

周四上午 11 点 08 分，你收到了一个奇怪的 bug 报告："在线代码编辑器里按 Ctrl+S 保存代码，浏览器弹出了保存页面的对话框！"

你打开项目代码，这是一个在线 Markdown 编辑器，支持多种快捷键：Ctrl+S 保存文档，Ctrl+B 加粗文本，Ctrl+Z/Y 撤销重做。你当时的实现是监听 `keydown` 事件：

```javascript
const editor = document.querySelector('.editor');

editor.addEventListener('keydown', (event) => {
  // Ctrl+S: 保存
  if (event.ctrlKey && event.key === 's') {
    console.log('保存文档');
    saveDocument();
  }

  // Ctrl+B: 加粗
  if (event.ctrlKey && event.key === 'b') {
    console.log('加粗文本');
    applyBold();
  }

  // Ctrl+Z: 撤销
  if (event.ctrlKey && event.key === 'z') {
    console.log('撤销');
    undo();
  }
});
```

你测试了一下，按下 Ctrl+S 时，控制台确实输出了"保存文档"，但浏览器的保存页面对话框也弹出了。"我需要阻止浏览器的默认行为，" 你想。

你加了 `preventDefault()`：

```javascript
editor.addEventListener('keydown', (event) => {
  if (event.ctrlKey && event.key === 's') {
    event.preventDefault(); // 阻止浏览器保存页面
    console.log('保存文档');
    saveDocument();
  }

  if (event.ctrlKey && event.key === 'b') {
    event.preventDefault(); // 阻止浏览器的加粗快捷键
    console.log('加粗文本');
    applyBold();
  }
});
```

测试：按下 Ctrl+S，浏览器对话框没有弹出，控制台输出"保存文档"。"解决了！" 你准备关闭 bug 报告。

但前端组的老赵走过来说："你这样写有问题。Mac 用户用的是 Command 键，不是 Ctrl 键。而且你应该用 `event.code` 而不是 `event.key`。"

"为什么？" 你问。

## key vs code 的区别

老赵展示了 `key` 和 `code` 的区别：

```javascript
document.addEventListener('keydown', (event) => {
  console.log('key:', event.key);     // 字符值（受键盘布局影响）
  console.log('code:', event.code);   // 物理按键位置（不受键盘布局影响）
  console.log('keyCode:', event.keyCode); // 已废弃
});

// 按下键盘上的 A 键：
// 美式键盘:
//   key: 'a'（小写）或 'A'（Shift+A）
//   code: 'KeyA'
//
// 法语键盘（AZERTY 布局）:
//   key: 'q'（因为 AZERTY 布局的 A 位置是 Q）
//   code: 'KeyA'（物理位置仍是 A 键）

// 按下数字键 1：
// 主键盘区的 1:
//   key: '1'
//   code: 'Digit1'
//
// 小键盘区的 1:
//   key: '1'
//   code: 'Numpad1'
```

"所以 `code` 表示物理按键位置，" 老赵解释道，"`key` 表示实际输入的字符。对于快捷键，应该用 `code`，因为用户期望的是物理按键位置（比如 QWERTY 布局的左手位置），而不是字符含义。"

你重构了快捷键逻辑：

```javascript
editor.addEventListener('keydown', (event) => {
  // 跨平台的修饰键检测
  const modifier = event.ctrlKey || event.metaKey; // Windows/Linux 用 Ctrl，Mac 用 Command

  // Ctrl/Cmd + S: 保存
  if (modifier && event.code === 'KeyS') {
    event.preventDefault();
    console.log('保存文档');
    saveDocument();
  }

  // Ctrl/Cmd + B: 加粗
  if (modifier && event.code === 'KeyB') {
    event.preventDefault();
    console.log('加粗文本');
    applyBold();
  }

  // Ctrl/Cmd + Z: 撤销
  if (modifier && event.code === 'KeyZ') {
    event.preventDefault();
    console.log('撤销');
    undo();
  }

  // Ctrl/Cmd + Shift + Z: 重做
  if (modifier && event.shiftKey && event.code === 'KeyZ') {
    event.preventDefault();
    console.log('重做');
    redo();
  }
});
```

"这样写跨平台兼容，" 老赵说，"Windows 和 Mac 用户都能正常使用快捷键。"

## keydown、keypress、keyup 的时机

老赵继续展示三种键盘事件的区别：

```javascript
const input = document.querySelector('input');

// keydown: 按键被按下时触发（最早）
input.addEventListener('keydown', (event) => {
  console.log('1. keydown');
  console.log('  值（按下前）:', input.value);
  console.log('  key:', event.key);
});

// keypress: 字符键被按下时触发（已废弃）
input.addEventListener('keypress', (event) => {
  console.log('2. keypress（已废弃）');
  console.log('  charCode:', event.charCode);
});

// input: 输入值实际改变时触发
input.addEventListener('input', (event) => {
  console.log('3. input');
  console.log('  值（改变后）:', input.value);
});

// keyup: 按键被释放时触发（最晚）
input.addEventListener('keyup', (event) => {
  console.log('4. keyup');
  console.log('  值（改变后）:', input.value);
});

// 按下 A 键的完整流程:
// 1. keydown    value: ""    key: "a"
// 2. keypress   charCode: 97 （已废弃，不要用）
// 3. input      value: "a"
// 4. keyup      value: "a"
```

老赵特别强调："永远不要用 `keypress` 事件，它已经被废弃了。用 `keydown` 监听按键，用 `input` 监听输入值变化。"

你做了一个实验，测试特殊键：

```javascript
document.addEventListener('keydown', (event) => {
  console.log('key:', event.key);
  console.log('code:', event.code);

  // 字符键
  if (event.key.length === 1) {
    console.log('字符键:', event.key);
  }

  // 功能键
  if (event.key === 'Enter') {
    console.log('回车键');
  }
  if (event.key === 'Escape') {
    console.log('Esc 键');
  }
  if (event.key === 'Tab') {
    console.log('Tab 键');
  }
  if (event.key === 'Backspace') {
    console.log('退格键');
  }
  if (event.key === 'Delete') {
    console.log('Delete 键');
  }

  // 方向键
  if (event.key === 'ArrowUp') {
    console.log('上方向键');
  }
  if (event.key === 'ArrowDown') {
    console.log('下方向键');
  }
  if (event.key === 'ArrowLeft') {
    console.log('左方向键');
  }
  if (event.key === 'ArrowRight') {
    console.log('右方向键');
  }

  // 修饰键
  if (event.key === 'Control') {
    console.log('Ctrl 键');
  }
  if (event.key === 'Shift') {
    console.log('Shift 键');
  }
  if (event.key === 'Alt') {
    console.log('Alt 键');
  }
  if (event.key === 'Meta') {
    console.log('Meta 键（Win/Cmd）');
  }

  // F1-F12
  if (event.key.startsWith('F') && event.key.length <= 3) {
    console.log('功能键:', event.key);
  }
});
```

## 组合键的精确检测

老赵展示了如何精确检测组合键：

```javascript
document.addEventListener('keydown', (event) => {
  // Ctrl/Cmd + S
  if ((event.ctrlKey || event.metaKey) && event.code === 'KeyS') {
    if (!event.shiftKey && !event.altKey) {
      event.preventDefault();
      console.log('保存');
      save();
    }
  }

  // Ctrl/Cmd + Shift + S
  if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.code === 'KeyS') {
    if (!event.altKey) {
      event.preventDefault();
      console.log('另存为');
      saveAs();
    }
  }

  // Ctrl/Cmd + Alt + S
  if ((event.ctrlKey || event.metaKey) && event.altKey && event.code === 'KeyS') {
    if (!event.shiftKey) {
      event.preventDefault();
      console.log('保存所有');
      saveAll();
    }
  }

  // Ctrl/Cmd + Shift + Alt + S
  if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.altKey && event.code === 'KeyS') {
    event.preventDefault();
    console.log('保存为模板');
    saveAsTemplate();
  }

  // 单独的 Escape 键（不能有修饰键）
  if (event.key === 'Escape' && !event.ctrlKey && !event.shiftKey && !event.altKey && !event.metaKey) {
    console.log('关闭对话框');
    closeDialog();
  }
});
```

"注意检查所有修饰键的状态，" 老赵说，"避免快捷键冲突。比如用户想按 Ctrl+S，但不小心按了 Ctrl+Shift+S，如果你的代码没有检查 `shiftKey`，两个快捷键都会触发。"

## 重复触发的处理

你注意到一个问题：长按一个键时，`keydown` 事件会不断重复触发。老赵展示了如何处理：

```javascript
let isKeyPressed = false;

document.addEventListener('keydown', (event) => {
  // 检查是否是重复触发
  if (event.repeat) {
    console.log('按键重复触发');
    return; // 忽略重复触发
  }

  // 或者用标志位防止重复执行
  if (isKeyPressed) {
    return;
  }

  isKeyPressed = true;
  console.log('按键首次按下');

  // 执行操作
  handleKeyPress(event);
});

document.addEventListener('keyup', (event) => {
  isKeyPressed = false;
  console.log('按键释放');
});

// 实际应用：游戏控制
const keys = {};

document.addEventListener('keydown', (event) => {
  if (event.repeat) return; // 忽略重复

  keys[event.code] = true;

  if (keys['KeyW']) {
    console.log('向前移动');
  }
  if (keys['KeyS']) {
    console.log('向后移动');
  }
  if (keys['KeyA']) {
    console.log('向左移动');
  }
  if (keys['KeyD']) {
    console.log('向右移动');
  }
});

document.addEventListener('keyup', (event) => {
  keys[event.code] = false;
});

// 游戏循环
setInterval(() => {
  if (keys['KeyW']) {
    moveForward();
  }
  if (keys['KeyS']) {
    moveBackward();
  }
  // ...
}, 16); // 60fps
```

## 输入法问题

老赵提醒："处理键盘输入时，还要注意输入法。中文、日文、韩文等语言使用输入法时，键盘事件的行为会不同。"

他展示了输入法相关的事件：

```javascript
const input = document.querySelector('input');

// compositionstart: 输入法开始输入
input.addEventListener('compositionstart', (event) => {
  console.log('输入法启动');
  console.log('data:', event.data); // 当前输入的内容
});

// compositionupdate: 输入法输入内容变化
input.addEventListener('compositionupdate', (event) => {
  console.log('输入法更新:', event.data);
});

// compositionend: 输入法完成输入
input.addEventListener('compositionend', (event) => {
  console.log('输入法结束:', event.data);
});

// 实际应用：搜索框自动补全
let isComposing = false;

input.addEventListener('compositionstart', () => {
  isComposing = true;
});

input.addEventListener('compositionend', () => {
  isComposing = false;
  // 输入法完成后再触发搜索
  performSearch(input.value);
});

input.addEventListener('input', (event) => {
  if (isComposing) {
    console.log('输入法输入中，不触发搜索');
    return;
  }

  // 非输入法输入，立即搜索
  performSearch(input.value);
});
```

"如果不处理输入法，" 老赵说，"用户在输入中文拼音的过程中，你的搜索函数会被频繁触发，导致性能问题和体验问题。"

## 快捷键管理器

老赵展示了一个完整的快捷键管理器实现：

```javascript
class KeyboardShortcuts {
  constructor() {
    this.shortcuts = new Map();
    this.init();
  }

  init() {
    document.addEventListener('keydown', (event) => {
      const shortcut = this.getShortcutKey(event);
      const handler = this.shortcuts.get(shortcut);

      if (handler) {
        event.preventDefault();
        handler(event);
      }
    });
  }

  // 生成快捷键字符串
  getShortcutKey(event) {
    const parts = [];

    if (event.ctrlKey || event.metaKey) parts.push('Ctrl');
    if (event.altKey) parts.push('Alt');
    if (event.shiftKey) parts.push('Shift');
    parts.push(event.code);

    return parts.join('+');
  }

  // 注册快捷键
  register(shortcut, handler) {
    // 标准化快捷键字符串
    // "Ctrl+S" 或 "Cmd+S" -> "Ctrl+KeyS"
    const normalized = this.normalizeShortcut(shortcut);
    this.shortcuts.set(normalized, handler);
  }

  normalizeShortcut(shortcut) {
    // "Ctrl+S" -> "Ctrl+KeyS"
    // "Cmd+Shift+Z" -> "Ctrl+Shift+KeyZ"
    let normalized = shortcut
      .replace(/Cmd/g, 'Ctrl')
      .replace(/\+([A-Z])$/g, (match, letter) => `+Key${letter}`)
      .replace(/\+([0-9])$/g, (match, digit) => `+Digit${digit}`);

    return normalized;
  }

  // 注销快捷键
  unregister(shortcut) {
    const normalized = this.normalizeShortcut(shortcut);
    this.shortcuts.delete(normalized);
  }
}

// 使用快捷键管理器
const shortcuts = new KeyboardShortcuts();

shortcuts.register('Ctrl+S', () => {
  console.log('保存');
  save();
});

shortcuts.register('Ctrl+Shift+S', () => {
  console.log('另存为');
  saveAs();
});

shortcuts.register('Ctrl+Z', () => {
  console.log('撤销');
  undo();
});

shortcuts.register('Ctrl+Y', () => {
  console.log('重做');
  redo();
});

shortcuts.register('Ctrl+B', () => {
  console.log('加粗');
  applyBold();
});

shortcuts.register('Escape', () => {
  console.log('关闭对话框');
  closeDialog();
});

// 条件注册（只在编辑器内生效）
const editor = document.querySelector('.editor');

editor.addEventListener('keydown', (event) => {
  if (event.ctrlKey && event.code === 'KeyK') {
    event.preventDefault();
    console.log('插入链接（仅编辑器内）');
    insertLink();
  }
});
```

下午 3 点，你完成了编辑器的快捷键系统重构。所有快捷键都正常工作，Mac 和 Windows 用户都能使用，输入法不会干扰搜索功能。你给产品经理发消息："快捷键系统已优化，支持跨平台，修复了所有已知问题。"

## 键盘事件法则

**规则 1: 使用 code 而非 key 处理快捷键**

`event.key` 返回字符值，受键盘布局影响；`event.code` 返回物理按键位置，不受键盘布局影响。快捷键应该基于物理位置（`code`），而字符输入处理应该用字符值（`key`）。

```javascript
document.addEventListener('keydown', (event) => {
  // ✅ 快捷键：使用 code（物理位置）
  if ((event.ctrlKey || event.metaKey) && event.code === 'KeyS') {
    event.preventDefault();
    save(); // 在所有键盘布局下都是左手中排第二个键
  }

  // ✅ 字符判断：使用 key（字符值）
  if (event.key === 'Enter') {
    submitForm();
  }
  if (event.key === 'Escape') {
    closeDialog();
  }

  // ❌ 错误：用 key 做快捷键
  if (event.ctrlKey && event.key === 's') {
    // 在非 QWERTY 布局（如法语 AZERTY）上会失效
  }
});

// code 的命名规则
// 字母键: KeyA, KeyB, ..., KeyZ
// 数字键: Digit0, Digit1, ..., Digit9 (主键盘区)
// 小键盘: Numpad0, Numpad1, ..., Numpad9
// 方向键: ArrowUp, ArrowDown, ArrowLeft, ArrowRight
// 功能键: F1, F2, ..., F12
// 特殊键: Enter, Space, Tab, Backspace, Delete, Escape
```

**规则 2: 跨平台修饰键检测**

Windows/Linux 使用 Ctrl 键，Mac 使用 Command（Meta）键。使用 `event.ctrlKey || event.metaKey` 实现跨平台快捷键。

```javascript
document.addEventListener('keydown', (event) => {
  // ✅ 跨平台快捷键
  const modifier = event.ctrlKey || event.metaKey;

  if (modifier && event.code === 'KeyS') {
    event.preventDefault();
    save(); // Windows: Ctrl+S, Mac: Cmd+S
  }

  if (modifier && event.code === 'KeyC') {
    // copy(); // Windows: Ctrl+C, Mac: Cmd+C
  }

  // 平台特定逻辑（少用）
  if (event.metaKey && !event.ctrlKey) {
    console.log('Mac 用户');
  }

  if (event.ctrlKey && !event.metaKey) {
    console.log('Windows/Linux 用户');
  }

  // 修饰键状态
  console.log('Ctrl:', event.ctrlKey);   // Control 键
  console.log('Shift:', event.shiftKey); // Shift 键
  console.log('Alt:', event.altKey);     // Alt 键（Mac: Option）
  console.log('Meta:', event.metaKey);   // Win 键 / Mac Command 键
});
```

**规则 3: 精确检查修饰键避免快捷键冲突**

检查所有修饰键的状态，确保只有预期的组合键触发操作。避免 Ctrl+S 和 Ctrl+Shift+S 同时触发。

```javascript
document.addEventListener('keydown', (event) => {
  const modifier = event.ctrlKey || event.metaKey;

  // ✅ 精确匹配：Ctrl+S（无其他修饰键）
  if (modifier && event.code === 'KeyS' && !event.shiftKey && !event.altKey) {
    event.preventDefault();
    save();
    return;
  }

  // ✅ 精确匹配：Ctrl+Shift+S（无 Alt）
  if (modifier && event.shiftKey && event.code === 'KeyS' && !event.altKey) {
    event.preventDefault();
    saveAs();
    return;
  }

  // ✅ 精确匹配：单独的 Escape 键（无修饰键）
  if (event.key === 'Escape' && !event.ctrlKey && !event.shiftKey && !event.altKey && !event.metaKey) {
    closeDialog();
    return;
  }

  // ❌ 错误：不检查其他修饰键
  if (modifier && event.code === 'KeyS') {
    save();
    // ⚠️ Ctrl+S、Ctrl+Shift+S、Ctrl+Alt+S 都会触发
  }
});
```

**规则 4: 使用 repeat 属性处理长按**

长按按键时，`keydown` 事件会重复触发。使用 `event.repeat` 属性检测重复触发，避免重复执行操作。

```javascript
document.addEventListener('keydown', (event) => {
  // ✅ 忽略重复触发
  if (event.repeat) {
    console.log('按键重复触发，忽略');
    return;
  }

  console.log('按键首次按下');
  handleKeyPress(event);
});

// 游戏控制：持续检测按键状态
const keys = new Set();

document.addEventListener('keydown', (event) => {
  if (event.repeat) return; // 忽略重复
  keys.add(event.code);
});

document.addEventListener('keyup', (event) => {
  keys.delete(event.code);
});

// 游戏循环
function gameLoop() {
  if (keys.has('KeyW')) moveForward();
  if (keys.has('KeyS')) moveBackward();
  if (keys.has('KeyA')) moveLeft();
  if (keys.has('KeyD')) moveRight();
  if (keys.has('Space')) jump();

  requestAnimationFrame(gameLoop);
}

gameLoop();
```

**规则 5: 处理输入法的 composition 事件**

中文、日文、韩文等输入法输入时，需要等待 `compositionend` 事件才执行搜索或验证，避免在拼音输入过程中频繁触发。

```javascript
const input = document.querySelector('input');
let isComposing = false;

input.addEventListener('compositionstart', () => {
  isComposing = true;
  console.log('输入法启动');
});

input.addEventListener('compositionend', (event) => {
  isComposing = false;
  console.log('输入法完成:', event.data);

  // 输入法完成后再触发搜索
  performSearch(input.value);
});

input.addEventListener('input', (event) => {
  if (isComposing) {
    console.log('输入法输入中，跳过搜索');
    return;
  }

  // 非输入法输入（如粘贴、删除），立即搜索
  performSearch(input.value);
});

// ❌ 错误：不处理输入法
input.addEventListener('input', () => {
  performSearch(input.value);
  // ⚠️ 输入中文拼音"zhong"时，会触发5次搜索：z, zh, zho, zhon, zhong
});

// ✅ 正确：等待输入法完成
input.addEventListener('compositionend', () => {
  performSearch(input.value);
  // 只在用户选择"中"字后触发一次搜索
});
```

**规则 6: keydown 用于快捷键，input 用于输入值**

`keydown` 在按键按下时触发，适合快捷键；`input` 在输入值实际改变时触发，适合验证和搜索。废弃的 `keypress` 不要使用。

```javascript
const input = document.querySelector('input');

// ✅ keydown：快捷键处理
input.addEventListener('keydown', (event) => {
  // Enter 提交
  if (event.key === 'Enter') {
    event.preventDefault();
    submitForm();
  }

  // Escape 清空
  if (event.key === 'Escape') {
    input.value = '';
  }

  // Ctrl+A 全选
  if ((event.ctrlKey || event.metaKey) && event.code === 'KeyA') {
    event.preventDefault();
    input.select();
  }
});

// ✅ input：输入值变化处理
input.addEventListener('input', (event) => {
  console.log('输入值变化:', input.value);

  // 实时验证
  validateInput(input.value);

  // 自动补全
  showSuggestions(input.value);
});

// ❌ 不要用 keypress（已废弃）
input.addEventListener('keypress', (event) => {
  // ⚠️ 已废弃，不要使用
});

// 事件触发顺序
// 1. keydown（按键按下，值尚未改变）
// 2. input（值实际改变）
// 3. keyup（按键释放）
```

---

**记录者注**:

键盘是用户与网页交互的重要方式，快捷键、表单输入、游戏控制都依赖键盘事件。从物理按键到字符输入，浏览器经历了复杂的转换过程：`keydown` 捕获按键动作，`input` 捕获输入结果，`compositionend` 处理输入法完成。

关键在于区分 `code`（物理位置）和 `key`（字符值），前者用于快捷键，后者用于字符判断。跨平台修饰键检测（`ctrlKey || metaKey`）让快捷键在 Windows 和 Mac 上都能工作。精确检查所有修饰键避免快捷键冲突，处理 `repeat` 属性防止重复触发，处理 `composition` 事件避免输入法干扰。

记住：**`code` 用于快捷键，`key` 用于字符；`ctrlKey || metaKey` 跨平台；精确检查修饰键；处理输入法 composition 事件。键盘事件是高效交互的基础**。
