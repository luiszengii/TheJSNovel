《第9次记录：数据通道泄露事故 —— data-* 属性的正确使用》

---

## 事故现场

周三上午十点，你盯着显示器上的产品列表页面，手指在键盘上敲击着。办公室里很安静，只有空调的嗡嗡声。窗外的阳光透过百叶窗洒在桌面上。

你的团队正在开发一个电商网站，产品列表页面需要存储每个商品的ID、价格、库存等信息，以便用户点击时快速响应。你决定把这些数据存储在HTML中：

```html
<div class="product" id="123" price="99.99" stock="50" category="electronics">
    <h3>商品名称</h3>
    <button onclick="addToCart(123, 99.99)">加入购物车</button>
</div>
```

代码工作正常，你继续添加更多字段：SKU、供应商ID、促销标签、推荐权重...HTML属性越来越多。直到QA发现了一个严重问题：

上午十一点半，QA小李走过来："这个页面在W3C验证器中有138个错误，"她把截图发到了你的Slack，"`price`、`stock`、`category` 都不是有效的HTML属性。"

你的手停在了键盘上，心里一紧。

中午十二点，安全顾问老张发来了一封标记为"高优先级"的邮件，指出：你把内部的数据结构暴露在了HTML中。竞争对手只需要右键"查看源代码"，就能获取你的定价策略、库存数据、甚至供应商关系。

你尝试把数据移到JavaScript对象中：

```javascript
const productData = {
    '123': { price: 99.99, stock: 50, category: 'electronics' }
};
```

但这样又带来新问题：HTML和JavaScript的数据分离了，每次添加商品都需要在两个地方维护数据。而且你的模板引擎是服务器端的，生成JavaScript对象很麻烦。

"一定有更好的方案，"你想，"能在HTML中存储数据，又不违反规范，还能保持一定的私密性..."

---

## 深入迷雾

下午一点，你在工位上搜索解决方案，手心微微出汗。产品经理发来消息："这个功能下午四点要演示给客户，能按时完成吗？"

"在看了，"你快速回复，但心里没底。

你在MDN上搜索"HTML custom attributes"，发现了 `data-*` 属性。这是HTML5引入的标准机制，专门用于在元素上存储自定义数据。

"就是这个！"你低声说道。

你开始重构代码：

```html
<!-- ❌ 旧代码：使用非标准属性 -->
<div class="product" id="123" price="99.99" stock="50">

<!-- ✅ 新代码：使用data-*属性 -->
<div class="product" data-id="123" data-price="99.99" data-stock="50">
```

W3C验证器不再报错。你测试了JavaScript访问方式：

```javascript
const product = document.querySelector('.product');

// 方式1：getAttribute（传统方式）
console.log(product.getAttribute('data-id'));     // "123"
console.log(product.getAttribute('data-price'));  // "99.99"

// 方式2：dataset（现代方式）
console.log(product.dataset.id);     // "123"
console.log(product.dataset.price);  // "99.99"
console.log(product.dataset.stock);  // "50"
```

`dataset` API自动处理了 `data-` 前缀，并且支持驼峰命名：

```html
<div data-user-id="123" data-user-role="admin"></div>
```

```javascript
const div = document.querySelector('div');
console.log(div.dataset.userId);    // "123"（驼峰命名）
console.log(div.dataset.userRole);  // "admin"
```

你发现了一个重要限制——`dataset` 中的所有值都是字符串：

```javascript
product.dataset.price = 99.99;
console.log(typeof product.dataset.price);  // "string"
console.log(product.dataset.price);         // "99.99"

// 需要手动转换类型
const price = parseFloat(product.dataset.price);  // 99.99（number）
const stock = parseInt(product.dataset.stock);     // 50（number）
```

你尝试存储复杂数据结构：

```javascript
// ❌ 错误：直接存储对象
const config = { theme: 'dark', lang: 'zh-CN' };
product.dataset.config = config;
console.log(product.dataset.config);  // "[object Object]"（无效）

// ✅ 正确：序列化为JSON
product.dataset.config = JSON.stringify(config);
console.log(product.dataset.config);  // '{"theme":"dark","lang":"zh-CN"}'

// 读取时反序列化
const savedConfig = JSON.parse(product.dataset.config);
console.log(savedConfig.theme);  // "dark"
```

但你发现了安全问题：虽然数据存储在HTML中，任何人都能在DevTools或源代码中看到。你做了个测试：

```html
<div data-api-key="sk_live_abc123"></div>
```

右键查看源代码——API密钥明明白白地显示在那里。

你意识到 `data-*` 属性不是加密存储，而是**约定俗成的命名空间**。它解决的是"如何合法地在HTML中存储自定义数据"，而不是"如何隐藏数据"。

你研究了 `data-*` 的命名规则：

```javascript
// ✅ 有效的命名
<div data-id="123"></div>
<div data-user-name="张三"></div>
<div data-product-sku="ABC-123"></div>

// ❌ 无效的命名
<div data-123="value"></div>         <!-- 不能以数字开头 -->
<div data-my@attr="value"></div>     <!-- 不能包含特殊字符 -->
<div dataid="value"></div>           <!-- 必须有连字符 -->

// 驼峰命名自动转换
element.dataset.userName = 'test';
console.log(element.getAttribute('data-user-name'));  // "test"
```

---

## 真相浮现

下午三点半，你终于理清了思路，手指在键盘上快速敲击着。

你制定了新的数据存储策略：

**公开数据用 `data-*`**：

```html
<article data-article-id="456" data-category="tech" data-author="张三">
    <!-- 这些是可以公开的元数据 -->
</article>
```

**敏感数据用JavaScript**：

```javascript
// 服务器端渲染时注入到script标签中
const sensitiveData = {
    userId: '123',
    sessionToken: 'xxx',
    permissions: ['read', 'write']
};
```

**临时数据用property**：

```javascript
// 运行时计算的数据，不需要持久化
element.tempData = { lastUpdate: Date.now() };
```

你创建了数据存储的最佳实践示例：

```html
<!DOCTYPE html>
<html>
<head>
    <title>产品列表</title>
</head>
<body>
    <!-- 产品卡片 -->
    <div class="product-card"
         data-product-id="123"
         data-name="无线耳机"
         data-category="电子产品"
         data-public-price="299">
        <h3>无线耳机</h3>
        <p class="price">¥299</p>
        <button class="add-to-cart">加入购物车</button>
    </div>

    <script>
    // 敏感数据在JavaScript中
    const productDetails = {
        '123': {
            cost: 120,           // 成本（不应暴露）
            stock: 50,           // 真实库存
            supplierId: 'S001',  // 供应商信息
            margin: 0.59         // 利润率
        }
    };

    // 读取data-*属性
    document.querySelectorAll('.product-card').forEach(card => {
        const productId = card.dataset.productId;
        const publicPrice = parseFloat(card.dataset.publicPrice);

        // 获取敏感数据
        const details = productDetails[productId];

        card.querySelector('.add-to-cart').addEventListener('click', () => {
            addToCart({
                id: productId,
                name: card.dataset.name,
                price: publicPrice,
                // 不要把敏感数据暴露给用户
                // cost: details.cost,  // ❌ 不要这样做
            });
        });
    });
    </script>
</body>
</html>
```

你整理了 `data-*` 属性的典型用例：

下午四点，你把重构后的代码演示给产品经理："数据存储问题已解决，W3C验证全部通过，安全隐患也修复了。"

产品经理满意地点点头："很好，准备给客户演示吧。"

你靠在椅背上，长长地呼出一口气。`data-*` 属性，原来是HTML为自定义数据开辟的合法通道。

```javascript
// 用例1：状态管理
<button data-state="inactive" data-loading="false">
    点击我
</button>

button.addEventListener('click', async () => {
    button.dataset.loading = 'true';  // 修改状态
    await fetchData();
    button.dataset.loading = 'false';
});

// 用例2：配置参数
<div class="chart"
     data-type="line"
     data-labels='["Jan","Feb","Mar"]'
     data-values='[10,20,30]'>
</div>

const chart = document.querySelector('.chart');
const config = {
    type: chart.dataset.type,
    labels: JSON.parse(chart.dataset.labels),
    values: JSON.parse(chart.dataset.values)
};

// 用例3：关联数据
<button data-action="delete" data-target-id="123">删除</button>

button.addEventListener('click', () => {
    const action = button.dataset.action;
    const targetId = button.dataset.targetId;
    performAction(action, targetId);
});

// 用例4：CSS选择器
<div data-theme="dark" data-size="large">

<!-- CSS中使用attribute选择器 -->
[data-theme="dark"] {
    background: #000;
    color: #fff;
}

[data-size="large"] {
    font-size: 1.5rem;
}
```

---

## 世界法则

**世界规则 1：data-* 是 HTML5 的标准自定义属性机制**

`data-*` 属性允许你在HTML元素上存储任意数据，不会违反HTML规范：

```html
<!-- ✅ 符合规范 -->
<div data-user-id="123" data-role="admin"></div>

<!-- ❌ 不符合规范 -->
<div user-id="123" role-custom="admin"></div>
```

**命名规则**：
- 必须以 `data-` 开头
- 后面只能包含字母、数字、连字符、点、冒号、下划线
- 不能以 `xml` 开头
- 不能包含大写字母（HTML不区分大小写）

---

**世界规则 2：dataset API 提供便捷访问**

```javascript
const element = document.querySelector('.item');

// 读取
console.log(element.dataset.userId);    // 读取 data-user-id
console.log(element.dataset.userName);  // 读取 data-user-name

// 写入
element.dataset.userId = '456';     // 设置 data-user-id="456"
element.dataset.userName = '李四';  // 设置 data-user-name="李四"

// 删除
delete element.dataset.userId;      // 移除 data-user-id 属性

// 检查
if ('userId' in element.dataset) {  // 检查是否存在
    // ...
}
```

**驼峰命名自动转换**：
- `data-user-name` ↔ `dataset.userName`
- `data-product-id` ↔ `dataset.productId`

---

**世界规则 3：dataset 中的值永远是字符串**

```javascript
element.dataset.count = 123;
console.log(typeof element.dataset.count);  // "string"
console.log(element.dataset.count);         // "123"

// 需要手动转换类型
const count = parseInt(element.dataset.count);          // number
const price = parseFloat(element.dataset.price);        // number
const isActive = element.dataset.active === 'true';     // boolean
const config = JSON.parse(element.dataset.config);      // object
```

---

**世界规则 4：data-* 不提供安全性**

`data-*` 属性在HTML源码和DevTools中完全可见：

```html
<!-- ❌ 不要存储敏感信息 -->
<div data-password="123456"></div>
<div data-api-key="sk_live_abc123"></div>
<div data-credit-card="1234-5678-9012-3456"></div>

<!-- ✅ 只存储公开或非敏感数据 -->
<div data-product-id="123"></div>
<div data-category="electronics"></div>
<div data-display-name="用户昵称"></div>
```

**敏感数据应该**：
- 存储在服务器端
- 通过AJAX按需获取
- 存储在JavaScript闭包中（不暴露到全局）

---

**世界规则 5：data-* 可用于 CSS 选择器**

```html
<div data-status="active">激活</div>
<div data-status="inactive">未激活</div>
```

```css
/* CSS中使用attribute选择器 */
[data-status="active"] {
    color: green;
}

[data-status="inactive"] {
    color: gray;
}

/* 检查属性存在 */
[data-loading] {
    opacity: 0.5;
    pointer-events: none;
}
```

---

**世界规则 6：何时使用 data-* vs JavaScript property**

**使用 data-* 的场景**：
```javascript
// 1. 需要在HTML中可见（服务器端渲染）
<div data-initial-state="collapsed">

// 2. 需要被CSS选择器使用
[data-theme="dark"] { background: black; }

// 3. 语义上是"配置"或"元数据"
<button data-action="submit" data-target="form-1">

// 4. 需要持久化（例如用户自定义属性）
element.dataset.customSetting = userConfig;
```

**使用 JavaScript property 的场景**：
```javascript
// 1. 运行时临时数据
element.tempCache = { ... };

// 2. 复杂对象（避免序列化开销）
element.controller = new Controller();

// 3. 敏感数据
element._internalState = { secret: 'xxx' };

// 4. 频繁更新的数据（性能更好）
element.frameCount = 0;
```

---

**世界规则 7：data-* 的性能考虑**

```javascript
// dataset 比 getAttribute 稍慢（有转换开销）

// 性能测试（仅供参考）
const element = document.querySelector('.item');

console.time('getAttribute');
for (let i = 0; i < 10000; i++) {
    element.getAttribute('data-id');
}
console.timeEnd('getAttribute');  // ~2ms

console.time('dataset');
for (let i = 0; i < 10000; i++) {
    element.dataset.id;
}
console.timeEnd('dataset');  // ~3ms
```

**建议**：
- 大多数情况下使用 `dataset`（更简洁）
- 性能关键路径可以使用 `getAttribute`
- 避免在循环中频繁读取 `dataset`，可以先缓存

```javascript
// ❌ 性能较差
for (let i = 0; i < 1000; i++) {
    doSomething(element.dataset.config);
}

// ✅ 性能更好
const config = element.dataset.config;
for (let i = 0; i < 1000; i++) {
    doSomething(config);
}
```

---

**事故档案编号**：DOM-2024-0809
**影响范围**：数据存储、HTML规范合规性、安全性
**根本原因**：使用非标准属性存储数据，或在 data-* 中存储敏感信息
**修复成本**：低（使用 data-* 替换自定义属性，迁移敏感数据）

这是DOM世界第9次被记录的数据通道泄露事故。`data-*` 是HTML为自定义数据开辟的合法通道，但通道是透明的，不是加密的。明白什么应该公开、什么应该隐藏，是使用这个通道的前提。
