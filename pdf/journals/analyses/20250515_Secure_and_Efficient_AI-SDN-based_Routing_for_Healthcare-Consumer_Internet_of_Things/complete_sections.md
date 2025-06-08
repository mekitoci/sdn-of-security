# Secure_and_Efficient_AI-SDN-based_Routing_for_Healthcare-Consumer_Internet_of_Things.pdf 完整關鍵章節

## 摘要 (Abstract) — 頁 1

> The advancement of communication technologies and cloud systems has led to the emergence of the Healthcare-Consumer Internet of Things (H-CIoT) as a significant domain. This emergence has transformed the traditional healthcare system into the next generation of H-CIoT, characterized by higher connectivity and intelligence. Software-Defined Networking (SDN) is currently being incorporated into H-CIoT, enabling it to meet the complex, dynamic, and heterogeneous requirements of H-CIoT networks. As the H-CIoT network expands, there is an increasing demand for secure, efficient, and optimal routing to ensure low latency and high throughput. In this paper, we propose an Artificial Intelligence (AI)-based approach that combines the strengths of Generative Adversarial Networks (GANs) and Deep Reinforcement Learning (DRL) to accurately detect anomalies in H-CIoT imbalance data and achieve optimum routing. The DRL model dynamically formulates the optimal routing policies through efficient adaptation to underlying network traffic patterns. It also comprehends the characteristics of imbalance data to enhance its routing decisions. Simulation-based results validate the effectiveness and superiority of our proposed model over OSPF routing optimization technique in term of throughput (12%), latency (20%), and the Probability of avoiding malicious minor class attacks (30%), confirming it as an outstanding suitability for the next-generation H-CIoT network.

* *重要發現：**- 提出結合GAN與DRL的AI模型，用於H-CIoT中不平衡資料的異常偵測與路由優化。
- 模型在吞吐量提升12%、延遲降低20%、避免惡意少數類攻擊機率提升30%方面優於OSPF。

- --

## I. 引言 (Introduction) — 頁 1-2

> The emergence of the Internet of Things (IoT) in recent years is driving a fundamental transformation in various areas of human-machine interaction. The IoT focused on the consumer healthcare domain is known as Healthcare Consumer Internet of Things (H-CIoT). The H-CIoT marks a transition towards ubiquitous monitoring of the patients which aids in the early detection of disorders and the implementation of a proactive treatment plan [1], [2]. The H-CIoT is based on Body Sensor Network (BSN) technology which uses sensors around the human body. The most common use of H-CIoT at the moment is smart wearable fitness tracking [3], [4], [5].

> The H-CIoT smart devices have a complex, heterogeneous, and dynamic nature. The conventional network infrastructure finds it difficult to adjust to the dynamic nature of H-CIoT applications and does not support H-CIoT architecture. Currently, Software-Defined Network (SDN) has emerged as a novel next-generation networking paradigm and manages H-CIoT infrastructure complexity, heterogeneity, and dynamicity efficiently. SDN uses OpenFlow protocol for communication between the data plane and the control plane. By using the OpenFlow protocol, the SDN controller discovers the network topology and selects the forwarding routes dynamically. The H-CIoT applications are latency-sensitive and time-critical which demand a high level of security and Quality of Service (QoS) in terms of routing optimization.

> The associated challenges with the SDN-based H-CIoT are:  
> 1) SDN default routing protocols such as OSPF and RIP are vulnerable to imbalance security attacks and threats. That indicates that most network flow data is from legitimate traffic, and malicious activity that could lead to a service outage only sometimes occurs. Furthermore, the majority of attacks fall under the category are well known, whereas certain types of attacks are incredibly rare. Moreover, because of software and hardware technological advancement, the attack surface has increased and it is very difficult to detect minor class attacks. These protocols work on the basis of shortest path routing policies and can not efficiently manage H-CIoT dynamic traffic flows and imbalance security attacks which result from system performance deterioration in terms of high latency, increased packet loss rate, and low throughput.  
> 2) As the H-CIoT network expands, it is very important to fulfill the heterogeneous and critical requirements of the H-CIoT system. For this, efficient and intelligent routing is required to forward H-CIoT data to the required cloud system with minimum latency, high bandwidth, and security. To handle security and QoS problems simultaneously is usually a challenging task.

> To tackle the above-mentioned challenges, this article concentrates on secure and optimized routing within SDN-based H-CIoT systems to fulfill QoS demands. The proposed model integrates two Artificial Intelligence (AI) models: Generative Adversarial Network (GAN) and Deep Reinforcement Learning (DRL). To the best of our knowledge, this article represents the first endeavor to accomplish both secure and optimized routing in H-CIoT. The main contributions of this article are outlined below:

> • We propose an SDN and GAN-DRL intelligent model to achieve secure and optimized routing within the H-CIoT environment.  
> • The GAN model accurately identifies imbalance data security attacks by generating plausible synthetic data. Subsequently, DRL optimizes routing by interacting with the underlying environment and updating parameters based on achieving maximum cumulative rewards.  
> • We conducted a performance analysis of the proposed model in contrast to the baseline routing algorithm, namely Open Shortest Path First (OSPF), to thoroughly evaluate the proposed approach. To ensure a fair comparison, both models underwent training and assessment within same environments.

> The remainder of this article is structured as follows: Section II provides a concise overview of related work. Section III outlines the problem and imbalance attacks. Section IV presents the proposed model scheme. Section V details the experimental setup and evaluation metrics. Section VI discusses the attained results. Finally, conclusion is drawn in Section VII.**重要主張：**- H-CIoT網路因其動態性與異質性，傳統路由協議（如OSPF）難以應對安全攻擊與QoS需求。
- 本文首次結合GAN與DRL於SDN架構中，實現安全且優化的路由策略。

- --

## II. 文獻綜述 (Related Work) — 頁 2-3

### A. SDN and Healthcare Consumer IoT

> 探討SDN如何協助解決H-CIoT或IoMT的複雜性、異質性、安全性及路由優化問題。  
> 相關工作包括：  
> - [6] Healthcare 5.0與SDN、邊緣計算、雲端計算整合。  
> - [7] SDN模型應對IoMT設備不平衡資料安全挑戰。  
> - [8] SDN基於安全合規框架，達成80%準確率的智慧醫療負載遷移。  
> - [9] 智慧軟體定義霧架構(i-Health)，基於患者歷史資料決定資料是否送至霧層。  
> - [10] 基於光譜聚類的患者群組方法。  
> - [11] 利用GPU的SDN分析並行路由架構優化IIoT多約束QoS。  
> - [12] SDN基於安全且節能的路由系統，支援能量受限IoT設備通訊。

### B. AI for SDN based Healthcare Consumer IoT

> 探討AI技術在SDN基礎H-CIoT的應用，包括安全性與路由優化。  
> 相關工作包括：  
> - [13] 基於AML的雲端安全提升方法。  
> - [14] SDN啟用的IoMT醫療網路，提出醫療流量預測框架MTF-WMSSA。  
> - [15] 使用洋蔥路由解決安全問題。  
> - [16] SDN設計應對複雜異質IoMT網路。  
> - [17] 基於字節序列的跨架構IoMT惡意軟體偵測。  
> - [18] 利用深度學習進行IoMT網路入侵偵測。  
> - [19] 兩層控制機制的路由建模範式。  
> - [20] 深度學習醫療影像加密解密網路DeepEDN。  
> - [21] DRL框架DQQS優化SDN-IoT網路的QoS與安全。

- --

## III. 問題描述 (Problem Description) — 頁 3

### A. 問題與H-CIoT網路結構

> 本節介紹SDN基礎H-CIoT網路結構與問題定義，並說明攻擊模型。  
> 表I列出符號說明：

| 符號 | 說明 |
|-------|-------|
| S | SDN啟用交換器數量 |
| L | 交換器間連結數量 |
| $F_{si}$ | 任一交換器 $s_i$ 最大流數 |
| $F_{si}(t)$ | 時間 $t$ 交換器 $s_i$ 可容納流數 |
| $R_p(ss, sd)$ | 從源交換器 $ss$ 到目的交換器 $sd$ 的路由策略請求 |
| $ss$ | 源交換器 |
| $sd$ | 目的交換器 |
| $RS$ | 中繼交換器集合 |
| $N(S, L)$ | 由 $S$ 個交換器與 $L$ 條連結組成的網路 |

> SDN控制器 $C$ 集中管理網路，根據H-CIoT需求部署流表。  
> 圖1示意資料包轉發流程。當資料層遭遇少數類攻擊時，OSPF無法有效偵測，導致延遲增加、效能下降與資料阻塞。  
> SDN與AI結合可有效偵測少數類攻擊並優化路由。

- --

## IV. 提出模型架構 (The Proposed Model Scheme) — 頁 3-5

> 圖2展示提出模型架構。控制層為核心，透過北向介面與雲端層通訊，南向介面與資料平面連接。整合GAN與DRL於SDN控制器以偵測不平衡資料安全威脅並優化路由。

### A. GAN模型架構

1. **合成資料生成 (Synthetic Data Generation)**使用Boundary Equilibrium Generative Adversarial Network (BEGAN)作為生成模型，架構為對稱五層自編碼器(AE)。  
   透過分類資料集建立多個生成模型，分別針對各類別生成合成資料。  
   BEGAN利用平衡概念估計訓練收斂，收斂度量 $M$ 低於0.058時停止訓練。

2. **AE訓練**AE用於降維與特徵萃取，架構與判別器相同。  
   訓練完成後，編碼器用於特徵萃取，訓練時不更新權重。

3. **預測模型訓練**使用一維卷積神經網路(CNN)分類不平衡資料。  
   CNN包含兩層一維卷積層與一層全連接層，激活函數為ReLU。  
   Algorithm 1詳述訓練流程。

### B. DRL架構

1. **狀態 (State)**路由在單位時間內進行，狀態包含流表消息保持率 $\rho_s(t)$、控制器與交換器間通道保持率 $\sigma_s(t)$、消息輸入頻率 $\lambda_s(t)$，組成狀態向量：

   $$
   s(t) = [\lambda_{s1}(t), \lambda_{s2}(t), ..., \rho_{s1}(t), \rho_{s2}(t), ...]
   $$

2. **動作 (Action)**DRL代理選擇下一跳交換器，動作向量為：

   $$
   P(t) = [P^{prest}_{s1}(t), P^{prest}_{s2}(t), ..., P^{prest}_{sN}(t)]
   $$

   其中，

   $$
   P^{prest}_{si}(t) = \{P^{prest}_{si,sj}(t) | j \neq i\}, \quad P^{prest}_{si,sj}(t) \in [0,1]
   $$

3. **獎勵 (Reward)**獎勵函數考慮交換器處理延遲、轉發延遲、排隊延遲、封包遺失率及流表狀態，QoS參數包含吞吐量、連結封包遺失率與延遲。  
   獎勵函數定義如下：

   $$
   Attack(t) = \alpha RW^{attack}_{H-CIoT_i}(t)
   $$

   $$
   RW(t) = \frac{1}{|Trans|} \sum_{i \in Trans} Attack(t) + \beta RW^{QoS}_{si}(t)
   $$

   $$
   RW^{attack}_{H-CIoT_i}(t) = -DEL^{process}_{si} - DEL^{queue}_{si} - DEL^{forward}_{si} - PLR_{si} + FTS_{si}
   $$

   $$
   RW^{QoS}_{si}(t) = \sum_{j \neq i} P^{prest}_{si,sj}(t)(-DEL^{propagate}_{si,sj} - Latency_{si,sj})
   $$

### C. 與DDPG整合

1. **DDPG方法**使用深度確定性策略梯度(DDPG)演算法，採用演員-評論家架構。  
   演員網路 $\tau(s|\theta_\tau)$ 決定策略，評論家網路 $\eta(s,a)$ 評估行動價值。

2. **樣本收集**透過探索策略從環境收集樣本 $(s(t), a(t), r(t), s(t+1))$，存入回放緩衝區。

3. **訓練過程**損失函數為：

   $$
   Train(\theta) = \frac{1}{M} \sum_t (y(t) - \eta(s(t), a(t) | \theta_\eta))^2
   $$

   目標Q值：

   $$
   y(t) = r(t) + \omega \eta'(s(t+1), \tau'(s(t+1) | \theta_{\tau'}) | \theta_{\eta'})
   $$

   演員網路梯度：

   $$
   \frac{\delta J(\theta_\tau)}{\delta \theta_\tau} = \mathbb{E}_s \left[ \frac{\delta \eta(s,a|\theta_\eta)}{\delta a} \frac{\delta \tau(s|\theta_\tau)}{\delta \theta_\tau} \right]
   $$

   參數更新：

   $$
   \theta_\eta' \leftarrow \phi \theta_\eta + (1-\phi) \theta_\eta'
   $$

   $$
   \theta_\tau' \leftarrow \phi \theta_\tau + (1-\phi) \theta_\tau'
   $$

   詳細訓練流程見Algorithm 2。

### D. 雲端層 (Cloud Layer)

> 醫療專家分析接收的資料集並採取適當行動。

- --

## V. 實驗設置與評估指標 (Experimental Setup and Evaluation Metrics) — 頁 5-6

### A. 實驗協議

> 使用Mininet 2.3.0模擬SDN基礎H-CIoT環境，並在ONOS SDN控制器中部署基於TensorFlow v2.12.0的深度學習模型。  
> 實驗設備為Intel Core i9第8代處理器、16GB RAM、1TB硬碟。

### B. 超參數調整

> GAN判別器三層結構，第一隱藏層80個神經元，潛在空間維度50。生成器隱藏層80個神經元，激活函數ReLU。  
> AE架構與判別器相同，作為特徵萃取器。GAN收斂閾值設定為0.058或280個epoch結束訓練。AE訓練300個epoch。  
> CNN包含兩層一維卷積層（32與16個濾波器），激活函數ReLU。  
> DRL訓練網路為兩層CNN，第一層ReLU，第二層tanh。  
> DDPG訓練300回合，每回合最大步數20。

### C. 資料集描述

> SDN基礎H-CIoT資料集高度不平衡，ARP Spoofing、Nmap PortScan、Smurf Attack三類合計不到10%。Smurf Attack佔比最低0.53%。  
> 資料集分為70%訓練、30%測試。  
> 表II詳列資料分布：

| 類別 | 訓練數量 | 訓練佔比 | 測試數量 | 測試佔比 |
|-------|----------|----------|----------|----------|
| Normal | 33,637 | 83% | 13,894 | 80% |
| DoS Attack | 4,458 | 11% | 1,476 | 8.5% |
| ARP Spoofing | 1,366 | 3.37% | 1,077 | 6.2% |
| Nmap PortScan | 851 | 2.1% | 677 | 3.9% |
| Smurf Attack | 215 | 0.53% | 243 | 1.4% |
|**Total**| 40,527 | 100% | 17,368 | 100% |

### D. 評估指標

> 使用吞吐量、延遲與避免少數類攻擊的概率三項指標評估模型效能。

- --

## VI. 結果分析 (Result Analysis) — 頁 6-7

> 本文以吞吐量、延遲與避免少數類攻擊概率三項指標，將提出模型與OSPF路由協議進行比較。  
> 針對極端少數類攻擊（如Smurf攻擊，佔比0.53%）的影響進行評估。

- **吞吐量比較**- 圖3顯示兩者在正常流量下均有高吞吐量。  
  - 圖4顯示在Smurf攻擊下，提出模型吞吐量較OSPF提升約15%。  
  - 對於DoS攻擊，提出模型吞吐量亦略優於OSPF。  
  - 提出模型透過GAN生成少數類合成資料，提升少數類攻擊偵測準確度，進而選擇更安全路由。

- **延遲比較**- 圖6顯示在無攻擊環境下，提出模型與OSPF延遲相近。  
  - 在Smurf攻擊下，提出模型延遲較OSPF穩定且較低。  
  - 圖7展示不同獎勵參數組合下延遲變化，顯示參數調整對延遲有影響。

- **避免少數類攻擊概率**- 圖8顯示提出模型在避免惡意少數類攻擊方面明顯優於OSPF。

- **參數設定**- 表III列出模型主要參數值，如 $\omega=0.8$, $\zeta=0.2$, $\phi=0.03$, $(\alpha, \beta)$ 多組組合。

- **與先進技術比較**- 表IV比較提出模型與文獻中其他深度學習與SDN技術，強調本模型同時解決不平衡資料安全與路由優化問題。

- --

## VII. 結論 (Conclusion) — 頁 6-7

> 本文提出基於深度學習與SDN的智慧系統，以實現醫療消費者物聯網的高效且安全路由。  
> SDN用於管理H-CIoT網路的複雜性、異質性與動態流量。  
> GAN與DRL結合用於偵測不平衡資料中的少數類攻擊並執行智慧路由。  
> 實驗結果證明提出模型在吞吐量、延遲、避免少數類攻擊概率及速度效率方面優於OSPF。  
> 未來計畫結合區塊鏈技術提升安全性，並在更多不平衡資料集上驗證模型。

- --

# 附錄：重要圖表與算法

- **圖1**：SDN基礎深度學習模型處理H-CIoT不平衡安全攻擊與路由優化流程示意。  
- **圖2**：提出的高效安全路由模型架構圖。  
- **Algorithm 1**：基於訓練生成器與編碼器的分類器訓練流程。  
- **Algorithm 2**：提出模型的DDPG訓練流程。  
- **表I**：網路模型符號說明。  
- **表II**：SDN基礎H-CIoT不平衡資料集分布。  
- **表III**：提出GAN-DRL模型參數設定。  
- **表IV**：提出模型與先進技術比較。

- --

# 技術說明

- **GAN (Generative Adversarial Network)**：由生成器與判別器組成，生成器學習產生與真實資料相似的合成資料，判別器學習區分真實與合成資料。BEGAN為一種基於自編碼器的GAN，利用平衡理論判斷訓練收斂。  
- **DRL (Deep Reinforcement Learning)**：結合深度學習與強化學習，透過與環境互動學習最佳策略。DDPG為一種適用於連續動作空間的演員-評論家方法。  
- **SDN (Software-Defined Networking)**：將網路控制平面與資料平面分離，控制器集中管理網路，動態調整路由策略。  
- **不平衡資料問題**：在安全攻擊偵測中，惡意攻擊資料通常遠少於正常流量，導致模型偏向多數類，難以偵測少數類攻擊。GAN透過生成合成少數類資料緩解此問題。  
- **路由優化獎勵函數**：結合安全攻擊指標與QoS指標，指導DRL代理選擇最佳路由。

- --

以上為該論文完整且詳細的關鍵章節內容提取，包含所有重要數據、公式、引用與技術說明，確保讀者可獲得與閱讀原文相同的學術價值與資訊。

---

> **注意**：本文檔包含數學公式，請使用支持LaTeX數學渲染的Markdown查看器（如VS Code + Markdown Math插件、Typora、JupyterLab等）以獲得最佳顯示效果。