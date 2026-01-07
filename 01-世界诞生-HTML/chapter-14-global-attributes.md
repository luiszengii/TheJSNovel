《第14次记录:全局属性的统治 —— 无处不在的通行证》

---

## 事故现场

周三上午十点，你正在实现一个拖拽功能,需要标记哪些元素可以被拖动。办公室里人声嘈杂，隔壁组在开站会。

你的第一反应是创建自定义属性:

```html
<div draggable="true">可拖动</div>
<img draggable="true" src="photo.jpg">
<p draggable="false">不可拖动</p>
```

测试后发现:div和img都能拖动,但p标签设置了`draggable="false"`却还是能被拖动。

上午十一点，前端同事老刘路过看了一眼："又在调拖拽？这个功能下午要演示给客户吧？"

"对，"你说，"但有些元素的拖拽行为不太对。"

你困惑地查看文档,发现`draggable`是一个标准的HTML全局属性,不是你自己创建的。而且它有特定的默认值规则:
- 大部分元素:默认`auto`(不可拖动)
- `<a>`和`<img>`与选中文本:默认可拖动
- `draggable="false"`只是建议,浏览器可能忽略

更让你惊讶的是,当你给一个按钮添加`hidden`属性时:

```html
<button hidden>隐藏按钮</button>
```

按钮消失了——但你并没有写CSS。你检查computed styles,发现浏览器自动添加了`display: none`。

"原来`hidden`是内置的全局属性,不是class?"

你开始怀疑:还有多少这样的"魔法属性"?

---

## 深入迷雾

上午十一点半，你开始系统地测试HTML的全局属性。首先是最常用的`id`和`class`:

```html
<div id="unique" class="box active">内容</div>
```

```javascript
// id: 唯一标识符
console.log(document.getElementById('unique'));  // 获取元素

// class: 多个类名,空格分隔
const element = document.querySelector('.box');
console.log(element.classList);  // DOMTokenList ["box", "active"]
```

然后你发现了`title`属性的行为:

```html
<button title="这是提示信息">悬停我</button>
```

鼠标悬停时,浏览器自动显示tooltip。不需要任何JavaScript或CSS。

你测试了`contenteditable`:

```html
<div contenteditable="true">点击编辑这段文字</div>
```

div变成了可编辑区域,像一个简易的富文本编辑器。

```javascript
element.addEventListener('input', (e) => {
    console.log('内容变化:', e.target.innerHTML);
});
```

你测试了`tabindex`:

```html
<div>普通div,不能获得焦点</div>
<div tabindex="0">可以Tab键访问</div>
<div tabindex="-1">只能通过JS获得焦点</div>
<div tabindex="1">Tab顺序第一个</div>
```

按Tab键时,浏览器按照tabindex数值顺序遍历元素。

然后你发现了`spellcheck`:

```html
<input type="text" spellcheck="true">
<textarea spellcheck="false"></textarea>
```

第一个输入框会标记拼写错误,第二个不会。

你测试了`translate`:

```html
<p translate="no">Google API Key: sk_abc123</p>
<p translate="yes">This will be translated</p>
```

`translate="no"`告诉翻译工具不要翻译这段内容。

更强大的是`data-*`属性:

```html
<div data-user-id="123" data-user-role="admin">用户信息</div>
```

```javascript
const div = document.querySelector('div');
console.log(div.dataset.userId);    // "123"
console.log(div.dataset.userRole);  // "admin"

// 修改
div.dataset.status = 'active';
console.log(div.getAttribute('data-status'));  // "active"
```

你发现了`lang`属性影响CSS:

```html
<style>
:lang(en) { quotes: '"' '"'; }
:lang(zh) { quotes: '「' '」'; }
</style>

<p lang="en"><q>Hello</q></p>  <!-- 显示: "Hello" -->
<p lang="zh"><q>你好</q></p>  <!-- 显示: 「你好」 -->
```

---

## 真相浮现

中午十二点，你终于搞清楚了HTML全局属性的完整体系。

你整理了全局属性的分类:

**类别1:标识与引用**

```html
<!-- id: 唯一标识符 -->
<div id="main">...</div>

<!-- class: 样式类名(多个) -->
<div class="container active">...</div>

<!-- slot: Web Components槽位名 -->
<slot name="header"></slot>
```

**类别2:元数据**

```html
<!-- title: 提示信息(tooltip) -->
<abbr title="HyperText Markup Language">HTML</abbr>

<!-- lang: 语言代码 -->
<html lang="zh-CN">

<!-- translate: 是否翻译 -->
<code translate="no">npm install</code>

<!-- dir: 文本方向 -->
<p dir="rtl">مرحبا</p>  <!-- 从右到左 -->
```

**类别3:交互行为**

```html
<!-- hidden: 隐藏元素 -->
<div hidden>不可见</div>

<!-- contenteditable: 可编辑 -->
<div contenteditable="true">可编辑内容</div>

<!-- draggable: 可拖动 -->
<div draggable="true">拖动我</div>

<!-- spellcheck: 拼写检查 -->
<input spellcheck="true">

<!-- tabindex: Tab键顺序 -->
<div tabindex="0">可聚焦</div>

<!-- accesskey: 快捷键 -->
<button accesskey="s">保存(Alt+S)</button>
```

**类别4:自定义数据**

```html
<!-- data-*: 自定义数据 -->
<div data-product-id="123" data-price="99.99">产品</div>
```

**类别5:ARIA无障碍**

```html
<!-- role: 语义角色 -->
<div role="navigation">导航</div>

<!-- aria-*: 无障碍属性 -->
<button aria-label="关闭">×</button>
<input aria-required="true" aria-invalid="false">
```

你创建了完整示例:

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>全局属性演示</title>
    <style>
        [hidden] { display: none; }
        .editable { border: 1px dashed #999; padding: 10px; }
        [draggable="true"] { cursor: move; }
        [tabindex] { outline: 2px solid blue; }
    </style>
</head>
<body>
    <h2>1. 基础标识属性</h2>
    <div id="container" class="box large" title="这是一个容器">
        鼠标悬停查看title
    </div>

    <h2>2. hidden属性</h2>
    <p>可见段落</p>
    <p hidden>隐藏段落</p>
    <button onclick="document.querySelector('[hidden]').hidden = false">
        显示隐藏段落
    </button>

    <h2>3. contenteditable</h2>
    <div class="editable" contenteditable="true">
        点击编辑这段文字
    </div>

    <h2>4. draggable</h2>
    <div draggable="true" style="width:100px;height:50px;background:lightblue;">
        拖动我
    </div>

    <h2>5. tabindex</h2>
    <div tabindex="1">Tab顺序: 1</div>
    <div tabindex="3">Tab顺序: 3</div>
    <div tabindex="2">Tab顺序: 2</div>
    <div tabindex="-1">不在Tab顺序中</div>

    <h2>6. spellcheck</h2>
    <input type="text" spellcheck="true" placeholder="拼写检查: 开启">
    <input type="text" spellcheck="false" placeholder="拼写检查: 关闭">

    <h2>7. data-*自定义属性</h2>
    <div id="user-card"
         data-user-id="123"
         data-user-name="张三"
         data-user-role="admin">
        用户卡片
    </div>

    <h2>8. translate</h2>
    <p>这段文字会被翻译</p>
    <p translate="no">API_KEY: sk_abc123</p>

    <h2>9. accesskey快捷键</h2>
    <button accesskey="s" onclick="alert('保存')">
        保存 (Alt+S)
    </button>

    <h2>10. ARIA无障碍</h2>
    <div role="navigation" aria-label="主导航">
        <button aria-label="关闭对话框">×</button>
    </div>

    <script>
        // data-*属性访问
        const userCard = document.getElementById('user-card');
        console.log('userId:', userCard.dataset.userId);
        console.log('userName:', userCard.dataset.userName);
        console.log('userRole:', userCard.dataset.userRole);

        // 修改data-*属性
        userCard.dataset.status = 'active';

        // draggable事件
        document.querySelector('[draggable]').addEventListener('dragstart', (e) => {
            console.log('开始拖动');
            e.dataTransfer.setData('text/plain', 'dragged data');
        });

        // contenteditable事件
        document.querySelector('[contenteditable]').addEventListener('input', (e) => {
            console.log('内容变化:', e.target.textContent);
        });
    </script>
</body>
</html>
```

你发现了全局属性的优先级和继承:

```html
<div lang="en">
    <p>English</p>
    <p lang="zh">中文</p>  <!-- 覆盖父元素的lang -->
</div>

<div contenteditable="true">
    <p>可编辑</p>
    <p contenteditable="false">不可编辑</p>  <!-- 覆盖父元素 -->
</div>
```

---

## 世界法则

**世界规则 1:全局属性可用于任何HTML元素**

**核心全局属性**:

```html
<!-- 标识 -->
id, class

<!-- 元数据 -->
title, lang, dir, translate

<!-- 行为 -->
hidden, contenteditable, draggable, spellcheck, tabindex, accesskey

<!-- 自定义 -->
data-*

<!-- 无障碍 -->
role, aria-*

<!-- 样式 -->
style
```

**使用示例**:

```html
<!-- 任何元素都可以使用这些属性 -->
<div id="app" class="container" hidden></div>
<span contenteditable="true"></span>
<img draggable="false" src="photo.jpg">
<p tabindex="0" role="button"></p>
```

---

**世界规则 2:id必须唯一,class可以重复**

```html
<!-- ✅ 正确: id唯一 -->
<div id="header"></div>
<div id="footer"></div>

<!-- ❌ 错误: id重复 -->
<div id="box"></div>
<div id="box"></div>  <!-- 无效! -->

<!-- ✅ 正确: class可以重复 -->
<div class="item"></div>
<div class="item"></div>

<!-- ✅ 正确: 多个类名 -->
<div class="item active selected"></div>
```

**JavaScript访问**:

```javascript
// getElementById只返回第一个匹配元素
document.getElementById('box');

// querySelectorAll返回所有匹配
document.querySelectorAll('.item');

// classList操作
element.classList.add('active');
element.classList.remove('inactive');
element.classList.toggle('selected');
element.classList.contains('active');
```

---

**世界规则 3:hidden属性等于display: none**

```html
<div hidden>隐藏内容</div>
<!-- 等价于 -->
<div style="display: none;">隐藏内容</div>
```

**特性**:
- 浏览器自动应用`display: none`
- 元素不占据空间
- 不触发事件
- 屏幕阅读器忽略

**JavaScript控制**:

```javascript
// 隐藏
element.hidden = true;
element.setAttribute('hidden', '');

// 显示
element.hidden = false;
element.removeAttribute('hidden');
```

**注意**:CSS可以覆盖

```css
/* ❌ 这样会让hidden失效 */
[hidden] {
    display: block !important;
}
```

---

**世界规则 4:contenteditable使元素可编辑**

```html
<div contenteditable="true">可编辑</div>
<div contenteditable="false">不可编辑</div>
<div contenteditable="inherit">继承父元素</div>
```

**行为**:
- 用户可以直接编辑内容
- 支持富文本编辑(粗体、斜体等)
- 可以粘贴图片和格式
- 触发input事件

**实现简易编辑器**:

```html
<div id="editor" contenteditable="true" style="border:1px solid;padding:10px;">
    编辑内容
</div>

<script>
const editor = document.getElementById('editor');

// 监听内容变化
editor.addEventListener('input', () => {
    console.log('内容:', editor.innerHTML);
});

// 获取纯文本
console.log(editor.textContent);

// 获取HTML
console.log(editor.innerHTML);

// 执行命令
document.execCommand('bold');        // 加粗
document.execCommand('italic');      // 斜体
document.execCommand('insertHTML', false, '<b>粗体</b>');
</script>
```

---

**世界规则 5:tabindex控制焦点顺序**

```html
<!-- tabindex > 0: 明确的Tab顺序 -->
<div tabindex="1">第一个</div>
<div tabindex="2">第二个</div>
<div tabindex="3">第三个</div>

<!-- tabindex="0": 自然顺序 -->
<div tabindex="0">跟随文档流</div>

<!-- tabindex="-1": 不在Tab序列,但可编程聚焦 -->
<div tabindex="-1" id="modal">模态框</div>
```

**规则**:
1. tabindex > 0: 按数值顺序访问(1, 2, 3...)
2. tabindex = 0: 按文档顺序访问
3. tabindex = -1: 不可Tab访问,但可通过JS聚焦

**最佳实践**:

```javascript
// ✅ 推荐: 使用0和-1
<div tabindex="0">...</div>  <!-- 可Tab访问 -->
<div tabindex="-1">...</div> <!-- 仅JS访问 -->

// ❌ 避免: 使用正数(破坏自然顺序)
<div tabindex="5">...</div>

// 编程聚焦
document.getElementById('modal').focus();
```

---

**世界规则 6:data-*存储自定义数据**

**命名规则**:
- 必须以`data-`开头
- 只能包含小写字母、数字、连字符、点、冒号、下划线
- 驼峰命名自动转换:`data-user-id` ↔ `dataset.userId`

```html
<div id="product"
     data-id="123"
     data-name="笔记本"
     data-price="5999"
     data-in-stock="true"
     data-tags='["电子产品","热卖"]'>
</div>
```

**JavaScript访问**:

```javascript
const product = document.getElementById('product');

// 读取
console.log(product.dataset.id);        // "123"
console.log(product.dataset.name);      // "笔记本"
console.log(product.dataset.price);     // "5999"
console.log(product.dataset.inStock);   // "true" (驼峰命名)
console.log(product.dataset.tags);      // '[...]'

// 写入
product.dataset.status = 'active';
product.dataset.lastUpdate = Date.now();

// 删除
delete product.dataset.status;

// 遍历
for (let key in product.dataset) {
    console.log(key, product.dataset[key]);
}
```

**CSS选择器**:

```css
/* 属性选择器 */
[data-status="active"] {
    color: green;
}

[data-price] {
    font-weight: bold;
}
```

---

**世界规则 7:title提供提示信息**

```html
<abbr title="HyperText Markup Language">HTML</abbr>
<button title="保存当前文档">💾</button>
<a href="..." title="跳转到首页">首页</a>
```

**行为**:
- 鼠标悬停时显示tooltip
- 延迟约1秒显示
- 浏览器原生样式(不可自定义)
- 对触摸设备无效

**注意**:

```html
<!-- ❌ 不要依赖title传递关键信息 -->
<button title="这是唯一的说明">?</button>

<!-- ✅ 使用title补充信息 -->
<button aria-label="帮助" title="获取帮助和文档">帮助</button>
```

---

**世界规则 8:lang影响语言处理**

```html
<html lang="zh-CN">
<p lang="en">Hello</p>
<p lang="ja">こんにちは</p>
```

**影响**:
- CSS伪类`:lang()`
- 拼写检查
- 语音合成
- 翻译工具
- 引号样式

**示例**:

```css
:lang(en) { quotes: '"' '"'; }
:lang(zh) { quotes: '「' '」'; }
:lang(fr) { quotes: '«' '»'; }

q:before { content: open-quote; }
q:after { content: close-quote; }
```

```html
<p lang="en"><q>Hello</q></p>  <!-- "Hello" -->
<p lang="zh"><q>你好</q></p>  <!-- 「你好」 -->
<p lang="fr"><q>Bonjour</q></p>  <!-- «Bonjour» -->
```

---

**世界规则 9:ARIA属性增强无障碍**

**常用ARIA属性**:

```html
<!-- role: 定义元素角色 -->
<div role="button">按钮</div>
<div role="navigation">导航</div>
<div role="alert">警告</div>

<!-- aria-label: 无障碍标签 -->
<button aria-label="关闭对话框">×</button>

<!-- aria-hidden: 对屏幕阅读器隐藏 -->
<span aria-hidden="true">🔒</span>

<!-- aria-live: 动态内容通知 -->
<div aria-live="polite" id="status">状态更新</div>

<!-- aria-required: 必填 -->
<input aria-required="true">

<!-- aria-invalid: 验证状态 -->
<input aria-invalid="true" aria-describedby="error">
<div id="error">邮箱格式错误</div>
```

**最佳实践**:

```html
<!-- ✅ 正确使用 -->
<button aria-label="关闭">×</button>
<nav role="navigation" aria-label="主导航">
    <a href="/">首页</a>
</nav>

<!-- ❌ 过度使用 -->
<div role="button" tabindex="0" aria-label="点击">
    <!-- 应该使用<button> -->
</div>
```

下午一点，你把完善后的拖拽功能提交了代码。所有全局属性都按照规范正确使用。

老刘路过时说："准备好演示了？"

"没问题，"你点点头，"全局属性的行为都搞清楚了。"

你靠在椅背上，长长地呼出一口气。全局属性是HTML元素的通行证，现在你已经掌握了它们的使用规则。

---

**事故档案编号**:DOM-2024-0814
**影响范围**:元素行为、无障碍、数据存储
**根本原因**:不理解全局属性的作用域和优先级
**修复成本**:低(理解规则后正确使用全局属性)

这是DOM世界第14次被记录的全局属性统治事故。全局属性是HTML元素的通行证——无论元素是什么类型,它们都能使用这些属性。它们定义了标识、行为、元数据、无障碍,是DOM世界最普遍的规则。理解它们,就理解了HTML元素的共同语言。
