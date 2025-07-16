# astrbot_plugin_push_lite

> [!caution]
> token切勿泄漏，如已泄漏请尽快修改。持有token者可令Bot发送任意文本消息。

Astrbot轻量级推送插件，提供api服务。目前仅支持发送文本消息和图片。

## 调用方法

> [!note]
> 目标会话标识可用/sid查看。/sid 指令返回的结果中的 SID 就是 umo 。

参数message_type可选配置如下

```
text: 纯文本
image: 纯图片
text_image: 前面文本后面追加图片
image_text: 前面图片后面追加文本
```

### **1. 发送消息(json)**  

**Endpoint:**  
`POST /send`  

**Headers:**  

- `Authorization: Bearer <API_TOKEN>`  

**Request Body (JSON):**  

```json
{
  "content": "消息内容或base64编码的图片",
  "umo": "目标会话标识",
  "message_type": "可选，消息类型，默认为text",
  "callback_url": "可选，处理结果回调URL",
  "images":"xxx,xxxx", // 图片链接列表，使用,分割
}
```

**Response:**  

```json
{
  "status": "queued",
  "message_id": "生成的消息ID",
  "queue_size": 1
}
```

---

### **2. 发送消息(form_data)**  

**Endpoint:**  
`POST /send_form`  

**Headers:**  

- `Authorization: Bearer <API_TOKEN>`  

**Request Body (Form):**  

```text
content=消息内容或base64编码的图片&umo=目标会话标识&message_type=可选，消息类型，默认为text&callback_url=可选，处理结果回调URL&images=xxx,xxxxx
```

**Response:**  

```json
{
  "status": "queued",
  "message_id": "生成的消息ID",
  "queue_size": 1
}
```

---

### **3. 健康检查**  

**Endpoint:**  
`GET /health`  

**Response:**  

```json
{
  "status": "ok",
  "queue_size": 1
}
```  

---

### **3. 回调通知格式（如果提供 `callback_url`）**  

**Method:** `POST`  

**Request Body (JSON):**  

```json
{
  "message_id": "原始消息ID",
  "success": true,
  "error": "可选，错误信息（仅在失败时返回）"
}
```

**成功示例:**  

```json
{
  "message_id": "123e4567-e89b-12d3-a456-426614174000",
  "success": true
}
```

**失败示例:**  

```json
{
  "message_id": "123e4567-e89b-12d3-a456-426614174000",
  "success": false,
  "error": "错误信息"
}
```

---

### **错误码**  

- **400**: 请求格式错误或缺少必要字段
- **403**: API 令牌无效
