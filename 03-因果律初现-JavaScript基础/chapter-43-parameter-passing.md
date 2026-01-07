《第43次记录:参数传递事故 —— 值传递与引用传递》

---

## 事故现场

周二上午,测试部门发来bug报告:"购物车结算金额计算错误,用户反馈价格不对。"

你打开代码,找到计算折扣的函数:

```javascript
function applyDiscount(price, discount) {
    price = price * discount
    console.log('折后价:', price)
    return price
}

let originalPrice = 100
let finalPrice = applyDiscount(originalPrice, 0.8)
console.log('原价:', originalPrice)
console.log('最终价:', finalPrice)
```

输出很正常:折后价80,原价100,最终价80。"没问题啊。"你困惑地说。

但测试又发来一个更奇怪的bug:"批量修改商品信息后,所有商品的原始数据都变了。"你找到批量修改的函数:

```javascript
function updateProduct(product) {
    product.discounted = true
    product.price = product.price * 0.8
    return product
}

const products = [
    { id: 1, name: '商品A', price: 100 },
    { id: 2, name: '商品B', price: 200 }
]

const discountedProducts = products.map(updateProduct)
```

你在控制台打印`products`,发现所有商品的价格都变成了折扣价——原价100的变成80,原价200的变成160!原始数据被修改了。

"为什么数字参数不会变,对象参数会变?"你盯着屏幕,手心开始冒汗。

客服群弹出消息:"用户投诉商品价格显示混乱,有的地方是原价,有的地方是折扣价。"技术主管发来消息:"立刻排查,这是数据准确性问题。"

你的手指悬停在键盘上方。到底是什么导致了这个差异?

---

## 深入迷雾

你创建了一个测试文件,决心搞清楚参数传递的机制。首先测试基本类型:

```javascript
function changeNumber(num) {
    num = 999
    console.log('函数内:', num)  // 999
}

let value = 10
console.log('调用前:', value)  // 10
changeNumber(value)
console.log('调用后:', value)  // 10 - 没变!
```

数字没有被修改。你明白了——基本类型传递的是值的副本,函数内修改副本不影响原值。

你测试对象:

```javascript
function changeObject(obj) {
    obj.name = 'Changed'
    console.log('函数内:', obj)  // { name: 'Changed' }
}

let person = { name: 'Original' }
console.log('调用前:', person)  // { name: 'Original' }
changeObject(person)
console.log('调用后:', person)  // { name: 'Changed' } - 变了!
```

对象被修改了!"引用类型传递的是引用的副本。"你写下笔记。

但你想起一个关键问题——如果在函数内重新赋值呢?

```javascript
function resetObject(obj) {
    obj.name = 'Modified'  // 修改属性
    obj = { name: 'Replaced' }  // 重新赋值
    console.log('函数内:', obj)  // { name: 'Replaced' }
}

let data = { name: 'Original' }
resetObject(data)
console.log('函数外:', data)  // { name: 'Modified' } - 不是Replaced!
```

"原来如此!"你恍然大悟。修改属性会影响外部对象,但重新赋值只是修改了函数内的引用副本,不影响外部的引用。

你测试了数组:

```javascript
function modifyArray(arr) {
    arr.push(4)  // 修改数组
    console.log('函数内push后:', arr)  // [1,2,3,4]

    arr = [5, 6, 7]  // 重新赋值
    console.log('函数内赋值后:', arr)  // [5,6,7]
}

let list = [1, 2, 3]
modifyArray(list)
console.log('函数外:', list)  // [1,2,3,4] - push生效,赋值无效
```

"修改属性生效,重新赋值无效。"你明白了JavaScript参数传递的本质——始终是值传递,基本类型传值,引用类型传引用的值。

你想起那个购物车bug。问题就在这里——函数直接修改了对象的属性,导致原始数据被污染。

---

## 真相浮现

你整理了参数传递的规则和最佳实践。

**问题代码:修改对象参数**

```javascript
// 危险:修改了原对象
function updateProduct(product) {
    product.discounted = true
    product.price = product.price * 0.8
    return product
}

const original = { id: 1, price: 100 }
const updated = updateProduct(original)

console.log(original.price)  // 80 - 原始数据被修改!
```

**正确做法:返回新对象**

```javascript
// 安全:返回新对象
function updateProduct(product) {
    return {
        ...product,
        discounted: true,
        price: product.price * 0.8
    }
}

const original = { id: 1, price: 100 }
const updated = updateProduct(original)

console.log(original.price)  // 100 - 原始数据未修改
console.log(updated.price)  // 80 - 新对象
```

**传递机制对比**

```javascript
// 基本类型:值复制
function changeNumber(num) {
    num = 999  // 修改副本
}
let value = 10
changeNumber(value)
console.log(value)  // 10 - 不变

// 引用类型:引用复制
function changeObject(obj) {
    obj.name = 'Changed'  // 通过引用修改
}
let person = { name: 'Original' }
changeObject(person)
console.log(person.name)  // 'Changed' - 被修改

// 重新赋值:不影响外部
function resetObject(obj) {
    obj = { name: 'New' }  // 只改变内部引用
}
resetObject(person)
console.log(person.name)  // 'Changed' - 不变
```

你把批量修改函数改成了这样:

```javascript
function updateProduct(product) {
    return {
        ...product,
        discounted: true,
        price: product.price * 0.8
    }
}

const products = [
    { id: 1, name: '商品A', price: 100 },
    { id: 2, name: '商品B', price: 200 }
]

const discountedProducts = products.map(updateProduct)

console.log(products[0].price)  // 100 - 原价保留
console.log(discountedProducts[0].price)  // 80 - 折扣价
```

测试通过。原始数据不再被修改,每个地方都能正确显示原价或折扣价。

---

## 世界法则

**世界规则 1:JavaScript是值传递**

```javascript
// 基本类型:复制值
function change(x) {
    x = 100  // 修改副本,不影响外部
}
let num = 10
change(num)
console.log(num)  // 10

// 引用类型:复制引用
function modify(obj) {
    obj.count = 1  // 通过引用修改,影响外部
}
const data = { count: 0 }
modify(data)
console.log(data.count)  // 1
```

**世界规则 2:修改属性vs重新赋值**

```javascript
function test(obj) {
    obj.a = 1  // ✓ 修改属性,影响外部
    obj = { a: 2 }  // ✗ 重新赋值,不影响外部
}

const o = { a: 0 }
test(o)
console.log(o.a)  // 1 (不是2)
```

**世界规则 3:避免副作用**

```javascript
// ❌ 不推荐:修改参数(副作用)
function addItem(arr) {
    arr.push(4)
    return arr
}

// ✅ 推荐:返回新值(纯函数)
function addItem(arr) {
    return [...arr, 4]
}
```

**世界规则 4:对象复制最佳实践**

```javascript
// 浅复制:适用于一层对象
function update(obj) {
    return { ...obj, updated: true }
}

// 深复制:适用于嵌套对象
function deepUpdate(obj) {
    return JSON.parse(JSON.stringify(obj))
}

// 或使用structuredClone (现代浏览器)
function cloneObject(obj) {
    return structuredClone(obj)
}
```

**世界规则 5:数组操作最佳实践**

```javascript
// ❌ 修改原数组
arr.push(4)
arr.sort()

// ✅ 返回新数组
const newArr = [...arr, 4]
const sorted = [...arr].sort()
```

---

**事故档案编号**:JS-2024-1643
**影响范围**:数据完整性、函数副作用、可预测性
**根本原因**:不理解参数传递机制导致意外修改原始数据
**修复成本**:中(需要重构函数,返回新对象)

这是JavaScript世界第43次被记录的参数传递事故。JavaScript始终是值传递——基本类型传值的副本,引用类型传引用的副本。修改对象属性会影响外部,重新赋值不会。推荐使用纯函数(无副作用),返回新对象而非修改参数。理解参数传递,就理解了JavaScript如何在函数间安全地传递和操作数据。
