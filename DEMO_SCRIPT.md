# Demo Script (口述稿)

> 录制时边操作边念。大约 3–4 分钟。每一步都标了你该在屏幕上做什么。

---

## 开场 (~15 秒)

**说：**
"Hey, this is my demo for the Week 7 assignment — microservice with service discovery. I'm going to show how a client can find running services through a registry without hardcoding any addresses. Let me walk through it."

---

## Part 1 — 环境准备 (~20 秒)

**操作：** 在终端里跑 venv 创建和 pip install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**说：**
"First I'll set up a virtual environment and install Flask and requests — those are the only two dependencies I need."

---

## Part 2 — 启动 Registry (~20 秒)

**操作：** 在 Terminal 1 跑 registry

```bash
python service_registry_improved.py
```

**说：**
"Now I'm starting the service registry on port 5001. This is from the professor's starter code — I kept it as-is because it already handles registration, heartbeats, and cleanup. All the services will register here."

---

## Part 3 — 启动 Instance 1 (~25 秒)

**操作：** 在 Terminal 2 跑 instance 1

```bash
python example_service.py user-service 8001
```

**说：**
"Here I'm starting the first instance of my user service on port 8001. You can see it prints a checkmark — that means it successfully registered itself with the registry. It also starts sending heartbeats every 10 seconds so the registry knows it's still alive."

---

## Part 4 — 启动 Instance 2 (~20 秒)

**操作：** 在 Terminal 3 跑 instance 2

```bash
python example_service.py user-service 8002
```

**说：**
"Same thing for instance 2, but on port 8002. Now the registry has two instances of user-service. These two instances don't know about each other at all — they only know the registry's address."

---

## Part 5 — 运行 Discovery Client (~40 秒)

**操作：** 在 Terminal 4 跑 discovery client

```bash
python discover_and_call.py user-service 5
```

**说：**
"Now here's the interesting part. I'm running my discovery client. It doesn't have any service address hardcoded — it just asks the registry: give me all the instances of user-service."

*(等输出出来后)*

"You can see it found 2 instances. Then it makes 5 calls, and each time it randomly picks one of the two instances. The `served_by` field in the response shows which instance actually handled each request — sometimes it's 8001, sometimes 8002. That's client-side load balancing through service discovery."

---

## Part 6 — 再跑一次，展示随机性 (~15 秒)

**操作：** 再跑一次同样的命令

```bash
python discover_and_call.py user-service 5
```

**说：**
"If I run it again, you'll see the results are different — different users, different instances getting picked. So the random selection is working."

---

## Part 7 — Graceful Shutdown (~25 秒)

**操作：** 在 Terminal 2（instance 1）按 Ctrl-C

**说：**
"Now let me show the graceful shutdown. When I hit Ctrl-C on instance 1, it sends a deregister request to the registry before shutting down. You can see the checkmark — it says deregistered successfully. So the registry won't try to send traffic to a dead instance."

---

## Part 8 — 关闭 Registry，收尾 (~15 秒)

**操作：** 在 Terminal 3 按 Ctrl-C 关掉 instance 2，然后在 Terminal 1 按 Ctrl-C 关掉 registry

**说：**
"And now I'll shut everything down. Instance 2 also deregisters cleanly. Finally I stop the registry. That's the full flow — registration, discovery, calling, and clean shutdown. Thanks for watching."

---

## 总时长：约 3 分钟

### 小提示
- 录制前先跑一遍确保没有报错
- 说话速度不用太快，正常语速就行
- 如果操作之间有等待时间（比如 pip install），可以剪掉
- 确保 4 个终端窗口都能在屏幕上同时看到，或者用分屏
