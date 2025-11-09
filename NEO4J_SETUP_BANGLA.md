# Neo4j Setup Guide - GitIntel এর জন্য 🚀

## কেন Neo4j দরকার? 🤔

GitIntel এর গ্রাফ ভিজুয়ালাইজেশন ফিচার ব্যবহার করতে Neo4j ডাটাবেজ লাগে। এটি ছাড়া GitIntel কাজ করবে, কিন্তু গ্রাফ দেখতে পারবেন না।

## ধাপে ধাপে Neo4j ইনস্টলেশন 📋

### ধাপ 1: Neo4j ডাউনলোড করুন
1. ব্রাউজারে যান: https://neo4j.com/download/
2. "Community Server" সিলেক্ট করুন
3. Windows ডাউনলোড করুন (neo4j-community-*-windows.zip)
4. ডাউনলোড হয়ে গেলে এক্সট্র্যাক্ট করুন (যেমন: C:\Neo4j)

### ধাপ 2: Neo4j কনফিগার করুন
1. Neo4j ফোল্ডারে যান (C:\Neo4j\bin)
2. `neo4j-admin.bat` রাইট ক্লিক করে "Run as Administrator" করুন
3. প্রথমবার রান করলে পাসওয়ার্ড সেট করতে বলবে - "password" লিখুন

### ধাপ 3: Neo4j সার্ভার স্টার্ট করুন
```cmd
# Command Prompt / PowerShell এ যান
cd C:\Neo4j\bin

# সার্ভার স্টার্ট করুন
neo4j start
```

সাকসেসফুল হলে দেখবেন:
```
Neo4j started successfully!
```

### ধাপ 4: এনভায়রনমেন্ট ভেরিয়েবল সেট করুন
GitIntel কে বলে দিতে হবে কোথায় Neo4j আছে। তিনটা ভেরিয়েবল সেট করুন:

#### অপশন 1: কমান্ড প্রম্পট (Temporary)
```cmd
set NEO4J_URI=bolt://localhost:7687
set NEO4J_USER=neo4j
set NEO4J_PASSWORD=password
```

#### অপশন 2: PowerShell (Temporary)
```powershell
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="password"
```

#### অপশন 3: Permanent (সিস্টেম ভেরিয়েবল)
1. Windows Search এ "environment variables" লিখুন
2. "Edit the system environment variables" ক্লিক করুন
3. "Environment Variables" বাটন ক্লিক করুন
4. "System variables" এর নিচে "New" ক্লিক করুন
5. এই তিনটা ভেরিয়েবল অ্যাড করুন:
   - `NEO4J_URI` = `bolt://localhost:7687`
   - `NEO4J_USER` = `neo4j`
   - `NEO4J_PASSWORD` = `password`

### ধাপ 5: Neo4j Browser চেক করুন
1. ব্রাউজারে যান: http://localhost:7474
2. Username: neo4j
3. Password: password
4. Connect ক্লিক করুন

যদি কাজ করে, তাহলে সেটাপ সাকসেসফুল!

## GitIntel চালান 🚀

```cmd
cd D:\GitIntel\GitIntelProject
python gitintel_desktop.py
```

Neo4j কানেক্টেড হলে দেখবেন: "🟢 Connected"
না হলে দেখবেন: "🔴 Offline Mode"

## ট্রাবলশুটিং 🔧

### সমস্যা 1: Port 7687 ব্যবহার হচ্ছে
```cmd
# দেখুন কোন প্রসেস পোর্ট ব্যবহার করছে
netstat -ano | findstr :7687

# প্রসেস কিল করুন (PID দিয়ে)
taskkill /PID <PID_NUMBER> /F
```

### সমস্যা 2: Neo4j স্টার্ট হচ্ছে না
```cmd
# লগ দেখুন
cd C:\Neo4j\logs
type neo4j.log
```

### সমস্যা 3: কানেকশন রিফিউজড
- Neo4j সার্ভার রানিং আছে কিনা চেক করুন
- Firewall এ port 7687 ব্লক করা আছে কিনা দেখুন

### সমস্যা 4: ভুল পাসওয়ার্ড
```cmd
# পাসওয়ার্ড রিসেট করুন
cd C:\Neo4j\bin
neo4j-admin set-initial-password newpassword
```

## গ্রাফ ভিজুয়ালাইজেশন দেখুন 👀

GitIntel অ্যানালাইসিস রান করার পর:
1. Neo4j Browser এ যান (http://localhost:7474)
2. এই কুয়েরি রান করুন:
```cypher
MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 100
```
3. গ্রাফ দেখুন - এটাই আপনার প্রজেক্টের রিলেশনশিপ ম্যাপ!

## সাকসেস চেকলিস্ট ✅

- [ ] Neo4j ডাউনলোড এবং ইনস্টল হয়েছে
- [ ] neo4j start কমান্ড সাকসেসফুল
- [ ] http://localhost:7474 এ ব্রাউজার ওপেন হয়
- [ ] Environment variables সেট হয়েছে
- [ ] GitIntel এ "🟢 Connected" দেখাচ্ছে
- [ ] অ্যানালাইসিস রান করে গ্রাফ তৈরি হয়েছে

সব গ্রিন হলে আপনার সেটাপ রেডি! 🎉