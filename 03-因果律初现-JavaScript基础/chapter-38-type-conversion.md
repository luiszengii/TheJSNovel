《第38次记录:类型转换事故 —— 隐式与显式的转换规则》

---

## 事故现场

周二下午,你在处理表单数据时遇到了计算错误:

```javascript
const price = "100"
const quantity = "2"
const total = price + quantity

console.log(total)  // "1002" - 什么?!期望200
```

你期望得到数字`200`,但得到了字符串`"1002"`。你改用减法:

```javascript
console.log("100" - "2")  // 98 - 这次是数字了
console.log("100" * "2")  // 200 - 乘法也转数字
```

减法和乘法自动转成了数字,但加法却变成了字符串拼接!"为什么加号特殊?"

你测试布尔值:

```javascript
console.log(true + 1)  // 2
console.log(false + 1)  // 1
console.log("5" - true)  // 4
```

布尔值在运算中自动变成了数字。你测试`==`和`===`:

```javascript
console.log(0 == false)  // true
console.log(0 === false)  // false
console.log("" == 0)  // true
console.log(null == undefined)  // true
```

`==`会转换类型,`===`不转换。你的同事路过:"JavaScript的类型转换很复杂,小心隐式转换的坑。"

---

## 深入迷雾

你开始系统学习类型转换规则。首先是显式转换:

```javascript
// Number()
Number("42")  // 42
Number("42px")  // NaN
Number(true)  // 1
Number(null)  // 0
Number(undefined)  // NaN

// String()
String(42)  // "42"
String(true)  // "true"
String(null)  // "null"

// Boolean()
Boolean(1)  // true
Boolean(0)  // false
Boolean("")  // false
Boolean("text")  // true
```

然后是隐式转换:

```javascript
// +运算符:有字符串就转字符串
"5" + 3  // "53"
5 + "3"  // "53"
true + "5"  // "true5"

// 其他运算符:转数字
"5" - 3  // 2
"5" * "3"  // 15
"10" / 2  // 5

// 比较运算符
"42" == 42  // true,转换后比较
0 == false  // true
"" == 0  // true
```

你测试了7个假值(Falsy):

```javascript
Boolean(false)  // false
Boolean(0)  // false
Boolean("")  // false
Boolean(null)  // false
Boolean(undefined)  // false
Boolean(NaN)  // false
Boolean(0n)  // false

// 其他都是真值
Boolean("0")  // true - 注意!非空字符串是真值
Boolean([])  // true
Boolean({})  // true
```

"原来如此!"你明白了转换规则。

---

## 真相浮现

你整理了类型转换的核心规则:

**+运算符的特殊性**

```javascript
// 有字符串 → 字符串拼接
"5" + 3  // "53"

// 无字符串 → 数字相加
5 + 3  // 8
true + 1  // 2
```

**其他运算符转数字**

```javascript
"5" - 3  // 2
"5" * 3  // 15
"10" / 2  // 5
```

**==vs===**

```javascript
// ==: 转换类型后比较
0 == false  // true
"" == 0  // true

// ===: 不转换,类型不同即false
0 === false  // false
"" === 0  // false

// 推荐:总是使用===
```

**7个假值**

```javascript
false, 0, "", null, undefined, NaN, 0n

// 其他都是真值
"0"  // true
[]  // true
{}  // true
```

你把表单计算改成了这样:

```javascript
const price = Number("100")
const quantity = Number("2")
const total = price * quantity

console.log(total)  // 200
```

问题解决了。

---

## 世界法则

**世界规则 1:显式转换**

```javascript
Number("42")  // 42
String(42)  // "42"
Boolean(1)  // true
```

**世界规则 2:+运算符的规则**

```javascript
// 有字符串 → 字符串
"5" + 3  // "53"

// 无字符串 → 数字
5 + 3  // 8
```

**世界规则 3:其他运算符转数字**

```javascript
"5" - 3  // 2
"5" * 3  // 15
"10" / 2  // 5
```

**世界规则 4:==vs===**

```javascript
0 == false  // true (转换类型)
0 === false  // false (不转换)

// 推荐:总是使用===
```

**世界规则 5:7个假值**

```javascript
false, 0, "", null, undefined, NaN, 0n

// 注意:这些是真值
"0", [], {}
```

---

**事故档案编号**:JS-2024-1638
**影响范围**:类型比较、运算结果、条件判断
**根本原因**:不理解隐式类型转换规则
**修复成本**:低(使用===,显式转换)

这是JavaScript世界第38次被记录的类型转换事故。JavaScript有显式转换和隐式转换。+运算符有字符串就转字符串,其他运算符转数字。==会转换类型,===不转换。7个假值:false、0、""、null、undefined、NaN、0n。理解类型转换,就理解了JavaScript如何在不同类型间自动转换。
