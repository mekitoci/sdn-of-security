# Physical_Assessment_of_an_SDN-Based_Security_Framework_for_DDoS_Attack_Mitigation_Introducing_the_SDN-SlowRate-DDoS_Dataset.pdf 完整關鍵章節

## 摘要 (Abstract)  
* *位置**：論文開頭，標題下方  
> Slow-read Distributed Denial of Service (DDoS) attacks are complex to detect and mitigate. Although existing tools allow one to identify these attacks, these tools mainly generate alerts. However, in real scenarios, a large number of attack detection alerts will put the security workforce in a bottleneck, as they will not be able to implement mitigation actions in a complete and timely manner. Furthermore, since most existing security solutions for DDoS attack mitigation are tested using datasets and simulated scenarios, their applicability to production networks could be unfeasible or ineffective due to possibly incomplete assumptions in their design. Therefore, automated security solutions against DDoS attacks are needed not only to be designed but also to be implemented and evaluated in real scenarios. This study presents a Software-Defined Networking (SDN)-based security framework, which automates the monitoring, detection, and mitigation of slow-rate DDoS attacks. The framework is implemented in a physical network that uses equipment from the European Experimental Facility Smart Networks for Industry (SN4I). The results demonstrate that the framework effectively mitigates malicious connections, with a mitigation efficiency between 91.66% – 100% for different conditions of the number of attackers and victims. In addition, the SDN-SlowRate-DDoS dataset is presented, which contains multiple experiments of slow-rate DDoS attacks performed on the real testbed. The resources provided in this security dataset are useful to the scientific and industry communities in designing and testing realistic solutions for intrusion detection systems.

* *重要發現**：  
- 提出一個基於SDN的自動化安全框架，能有效監控、檢測及緩解慢速率DDoS攻擊。  
- 在真實物理網路環境（SN4I設施）中實施並測試，緩解效率達91.66%至100%。  
- 發布了包含真實測試床慢速率DDoS攻擊實驗的SDN-SlowRate-DDoS數據集，促進現實入侵檢測系統的設計與測試。

- --

## I. 引言 (Introduction)  
* *位置**：摘要後，頁面46820起始  

> Distributed denial of service (DDoS) attacks cause critical complications in traditional and next-generation networks, such as the fifth-generation communication network (5G). Current solutions of intrusion detection systems (IDSs) alleviate part of the task to countermeasure these attacks, generating detection alerts to the security administration workforce [1]. However, given the huge amount of alerts these systems face, they could become useless, since humans will not be able to handle all alerts in a timely and complete way. Therefore, automated tools to mitigate DDoS attacks are more important than ever [2].  
> Various efforts have been made to create intelligent mechanisms to detect and mitigate DDoS attacks. Among the most promising solutions are those based on Software-Defined Networking (SDN) technology [3]. However, the lack of collaboration between academia and industry has obstructed the development of security tools that work effectively in production environments. As a result, most of the proposed security solutions have been tested using benchmark datasets or simulated environments [4], [5], [6]. Integrating these solutions into real networks could be unfeasible or ineffective due to potentially inappropriate assumptions considered in their design.  
> Most research groups and institutions do not have experimental facilities or a physical network to test their solutions and have reported the use of security datasets [7], [8]. However, most existing datasets contain synthetic data captured from simulated networks. Testing detection and mitigation systems with these datasets will result in ineffective or incomplete solutions when deployed in real scenarios. Therefore, a real testbed-based security dataset is fundamental for the design of realistic security solutions. Additionally, researchers interested in designing SDN-based security solutions do not have access to SDN-based datasets. That is, a dataset containing controller-based flow statistics is needed, such that researches can test centralized mechanisms based of these statistics.  
> In this study, we deploy and assess an automated framework to mitigate DDoS attacks. The framework includes a deep learning (DL)- based IDS to detect attacks and an intrusion prevention system (IPS) to autonomously mitigate detected attacks. The design of this framework is based on our previous study presented in [9] and [10]. Although this framework can be configured to detect any type of DDoS attacks, this study focuses on slow-rate DDoS which turn to be more recent and complex than high-rate DDoS attacks.  
> A relevant contribution of this study is that the performance of the proposed framework is showcased using physical equipment from the European facility Smart Networks for Industry (SN4I) [11]. In particular, a data center topology is configured using numerous microservers and minicomputers. The proposed automated framework demonstrates effectiveness on maximizing the attack connections mitigated when the number of attackers and victims are varied.  
> Another important contribution of this work is that we provide an SDN-based dataset for slow-rate DDoS attacks, named SDN-SlowRate-DDoS dataset. This dataset has two components: (i) raw pcap files and (ii) SDN controller-based network flow statistics, which contains traffic information from the real testbed based on SN4I. The resources of the provided dataset contribute to the development of realistic IDS solutions.  
> In summary, the contributions of this work are as follows.  
> 1) Realistic assessment of an automated DDoS attack mitigation framework using real equipment from the SN4I facility. The results demonstrated a mitigation efficiency between 91.66%–100% for different number of attackers and victims.  
> 2) SDN-based dataset for slow-rate DDoS attacks containing traffic generated using the SN4I facility. The dataset is named SDN-SlowRate-DDoS and is available on [12]. This dataset allows researchers to validate up-to-date realistic solutions of IDS.  
> The remainder of this paper is organized as follows. Section II explores similar work and highlights the contribution of this study. The proposed framework is described in Section III. Section IV reports the experimental results, including the generation of the SDN-based dataset and the evaluation of the framework. Section V discusses the findings of this study. Finally, the conclusion and future research are presented in Section VI.

* *重要主張**：  
- 現有IDS產生大量警報，人工難以及時處理，需自動化緩解工具。  
- 多數DDoS防禦方案僅在模擬環境或數據集上測試，缺乏真實網路驗證。  
- 本文提出基於SDN的自動化框架，結合深度學習IDS與IPS，並在真實SN4I設施中評估。  
- 發布包含真實SDN控制器流量統計的慢速率DDoS數據集，促進現實IDS設計。

- --

## II. 文獻綜述 (Similar Works)  
* *位置**：頁面46821起始  

### A. SDN-BASED DATASETS FOR SLOW-RATE DDoS ATTACKS  
> The existence of up-to-date security datasets is fundamental for the development of cutting-edge security solutions to secure traditional and next-generation networks from latest attacks. However, most existing DDoS security datasets contain traditional high-rate or volumetric DDoS attacks, such as TCP-SYN and UDP-flood attacks. These attacks are bandwidth intensive and large scale which use protocols from layer 3 and 4 to flood the network. Although these attacks are still critical to networks, many datasets are already available for researchers. That is the case of KDD99, NSL-KDD [13], ICMPv6-based dataset [14], LATAM-DDoS-IoT [15], CF2-based dataset [16], and CICDDoS2019 [17].  
> It is worth noting that a limited number of datasets include more recent and complex DDoS attacks, known as slow-rate DDoS attacks. Slow-rate DDoS attacks use application layer protocols to overwhelm servers. For example, in the slow HTTP read attack, a malicious user sends a pertinent number of connection requests to a victim server. Afterward, the user reads the server’s response slowly, but also preventing the server to incur in idle connection timeout. As a result, all server’s resources are occupied by the malicious user and denied to legitimate requests. CICDoS2017 dataset [18] is an example of a slow-rate DDoS dataset, which contains 24 hours of network traffic with six application layer DDoS attacks. In spite of providing real traces of most recent DDoS attacks, CICDoS2017 dataset is not oriented to SDN-based security applications. In contrast, among other resources, our dataset provides SDN controller-based statistics which serve to design and test security solutions specific for SDN environments.  
> Realistic datasets are also of relevant importance in designing and testing effective IDSs. Using simulated network-based datasets could not reflect realistic normal and attack scenarios, and researchers will find difficulties on developing effective and practical IDSs [16]. Most existing datasets captured samples from real testbed, for example, KDD99, NLS-KDD, LATAM-DDoS-IoT, CF20-based dataset, CICDDoS2019, and CICDoS2017. Nevertheless, different from our SDN-SlowRate-DDoS, no previous dataset used an SDN-based testbed with real equipment, which is of high importance to design security applications that are SDN-specific.  
> Table 1 compares the SDN-SlowRate-DDoS dataset with existing datasets. Unlike most existing datasets, the SDN-SlowRate-DDoS dataset contains the most recent DDoS attacks, namely slow-rate DDoS attacks. Additionally, different from previous datasets, our dataset is obtained using an SDN-based testbed. Furthermore, to promote the development of realistic IDSs, the data are captured from a testbed using real equipment. Finally, the resources provided by our dataset serves to design three types of realistic security solutions to slow-rate DDoS attacks: (i) packet statistics-based IDSs, (ii) Flow statistics-based IDSs, and (iii) SDN-specific IDSs.

### B. REALISTIC ASSESSMENT OF IPS  
> The use of datasets to evaluate IDSs is valuable. However, IPSs’ assessment requires network deployment. Although simulated networks, such as using Mininet [19], [20], are useful to effectively evaluate IPSs, they do not allow one to replicate real conditions, such as the behavior of legitimate traffic.  
> Different authors have recognized the importance of using real scenarios to validate their security solutions. An approach is to use real testbeds deployed with development board-based SDN switches, such as Zodiac FX [21], [22]. Although these devices are designed to be used in laboratories providing real traffic on physical hardware, these devices do not fulfill real conditions such as processing and memory capacity, and number of ports of real devices. Finally, more complete testbed, such as GENI [23], have helped the evaluation of security solutions [24]. These testbeds allow us to test the real-time capabilities of innovative security solutions.  
> In this study, SN4I facilities were used to evaluate a DDoS mitigation framework. SN4I runs on an Network Function Virtualization (NFV) and SDN-enabled network that interconnects the University of the Basque Country (UPV/EHU) with the Aeronautics Advanced Manufacturing Centre (CFAA) and the Rectorate of the University of the Basque Country. An isolated network slice was created over this infrastructure, including an external SDN controller to manage the created network. In this slice, the proposed framework which includes the IDS and IPS was tested, demonstrating its performance in real scenarios.

* *重要主張**：  
- 現有多數DDoS數據集聚焦高流量攻擊，缺乏慢速率DDoS及SDN環境數據。  
- 本文數據集獨特地基於真實SDN測試床，包含控制器流量統計，支持SDN特定安全方案設計。  
- IPS評估需真實網路環境，模擬環境無法完全反映合法流量行為。  
- SN4I設施提供真實NFV與SDN環境，適合安全框架實驗。

- --

## III. 研究方法 (DL-Based Framework for DDoS Mitigation)  
* *位置**：頁面46822起始  

> Figure 1 shows the proposed framework to detect and minimize DDoS attacks. The five elements of the architecture work as follows. The Routing module performs reactive traffic forwarding and traffic mirroring to the Monitor module. The Monitor processes network packets to obtain traffic flows using CICFlowMeter. These flows are identified by a five-tuple key: (Source IP, Source Port, Destination IP, Destination Port, Protocol), where IP refers to the Internet protocol address. Furthermore, each flow contains 76 features [18]. Feature selection and principal component analysis (PCA) are performed once the IDS receives the network flows. The IDS uses a trained DL model to classify each network flow as attack or legitimate. Then the IPS uses the IDS output to react against DDoS attacks. Particularly, the IPS decides the action to apply for each network connection. The actions are sent to the Flow Rule Manager, which translates them to flow rules that are installed in the data-plane devices (switches). The Flow Rule Manager continually communicates with the Routing module to avoid installing conflicted rules.

### A. DDoS ATTACK DETECTION  
> Some CICFlowMeter’s alternatives to monitor network traffic are Sflow and controller-based monitoring (e.g., Open Network Operating System ONOS statistics). One advantage of CICFlowMeter over other solutions is that it offers numerous significant features, which increase the IDS’ performance. Furthermore, this solution maintains network monitoring on the data plane, and the SDN controller is not overwhelmed with this task.  
> Using a DL model, the IDS identifies active network connections as malicious or legitimate. The IPS periodically consults this information that serves to define the appropriate mitigation actions.

### B. DDoS ATTACK MITIGATION  
> In the proposed mitigation strategy, attack connections are intended to be blocked permanently. In contrast, legitimate connections are contemplated not to be altered, blocked temporarily (if they are affected by the IDS’ false positives), or recovered (if they have been previously blocked). To this effect, the workflow of the mitigation strategy is depicted in Figure 2.  
> Four actions are considered in Figure 2: (i) No Action, (ii) Block Permanently a connection, (iii) Block Temporarily a connection, and (iv) Recover a connection. Furthermore, two lists are used to trace the connection’s states: PermanentlyBlocked[] which contains the connections blocked with a timeout of $\tau \gg 0$, and TemporarilyBlocked[] which contains the connections blocked for a limited number of time steps, $tbsteps$. These lists are initiated when the IPS is executed.  
> The mitigation strategy works as follows. For a given bidirectional connection $i,j$ that has been permanently blocked in a previous step, no action is taken since the IPS had defined a critical connection. Subsequently, if the connection has been temporarily blocked in a previous step, it is recovered once the temporary connection timeout $tbsteps$ is reached.  
> If the connection $i,j$ has not been previously blocked (temporarily or permanently), the IPS considers the information received from the IDS to decide among three options: Perform no action, block the connection temporarily, or block the connection permanently. In this sense, $mstate$ is defined for $i,j$ to define how critical the attack is for that connection as  
> $$
> mstate_{i,j} = \frac{1}{1 + e^{-(g_{i,j} - \eta)}},
> $$  
> where  
> $$
> g_{i,j} = \sum f_{i,j},
> $$  
> and $\eta$ helps set the threshold for a critical connection.  
> $f_{i,j}$ in (2) represents the vector of detection ($f_{i,j} = 1$) and non-detection ($f_{i,j} = 0$) in the period between $t$ – $t + 1t$.  
> If the connection has $mstate \leq \alpha$, it is considered non-critical and no action is executed. On the contrary, if the connection has $mstate > \alpha$, it is temporarily or permanently blocked. Roulette wheel selection is applied using $mstate$ to decide how to block the connection. Connections that are more critical have high values for $mstate$ (which means that there are many detection events for $i,j$ in the period $t$ – $t+1t$), and therefore have a higher chance of being permanently blocked.  
> Finally, Figure 3 shows the main process of the proposed mitigation method. The IDS is continuously consulted about the network connections. For all active connections, the mitigation strategy shown in Figure 2 is applied. Additionally, a permanently blocked connection is recovered each $\tau \gg 0$.  
> As the mitigation strategy is intended to work autonomously, the condition of recovering any connection after $t/\tau \geq 1$ helps increase the availability for legitimate connections affected by an IDS with a high false positive rate (FPR). Naturally, in this operation persistent attackers can be released. However, they will be detected by the IDS and blocked again by the mitigation strategy presented in Figure 2.  
> The IPS algorithm contains different parameters that can be estimated using experiments. In this work, after evaluating multiple alternatives, the parameters were set as $\tau = 10$ minutes, $tbsteps= 20$, $\eta = 3$, and $\alpha = 0.2$.

* *技術說明**：  
- **CICFlowMeter**：用於從網路封包中提取流量特徵，生成包含76個特徵的流量樣本。  
- **mstate計算**：使用sigmoid函數將攻擊檢測次數加權轉換為連續值，作為連接的攻擊嚴重度指標。  
- **Roulette wheel selection**：根據mstate值概率決定是否永久封鎖連接。  
- **IPS行動**：包括不動作、暫時封鎖、永久封鎖及恢復連接，並維護兩個封鎖列表以追蹤狀態。

- --

## IV. 實驗設計與結果 (Experiments and Results)  
* *位置**：頁面46823起始  

### A. 實驗設置 (Experimental Setup)  
> Figure 4 describes the experimental setup used to test the proposed framework on real SN4I equipment.  
> The configured data center contains two spine switches and four leaf switches. Two HP Aruba 3810M JL071A switches work as spine switches: SW Leioa and SW I2tLab2. Leaf switches VS1, VS2, VS3, and VS4 are virtual switches configured from the physical switch SW I2tLab1 (NEC IP8800/S3640-48T2XW). An additional switch VS5 is needed for traffic monitoring, which is a virtual switch configured from SW I2TLab1.  
> Each leaf switch is connected to both spine switches. Furthermore, traffic mirroring is performed only by leaf switches. A microserver is connected to the VS5 mirroring switch to capture and process network traffic.  
> ONOS controller is used to manage the SDN-based data center. The IDS and IPS servers are allocated on a different computer. The I2tLab router commands the management networks 10.98.2.0/24 and 10.98.1.0/24.  
> The testbed is configured with a set of microservers and minicomputers that run different services and clients. The configured network is 10.0.0.0/24 and contains 20 devices. Table 2 summarizes the equipment used in the experimental setup. Furthermore, Figure 5 shows a photo of the testbed of the SN4I infrastructure located at the Faculty of Engineering in Bilbao.

### B. 合法與攻擊流量 (Legitimate and Attack Traffic)  
> Table 3 shows the servers and clients configured in the data center to produce legitimate and attack traffic. Three Apache servers (.142, .132, and .91), which act as victim servers, are configured. The attackers are the minicomputers connected to the VS1 (.101, .102, .103, .104). Slowhttptest is used to attack Apache servers.  
> To generate legitimate traffic, various servers are deployed on the network. Two video streaming services are configured (on minicomputers .107 and .109) using VLC. Clients to these services are configured on the minicomputers .105 and .106. Similarly, two file transfer protocol (FTP) servers and several TCP and UDP servers based on Iperf and clients are deployed for these servers, as shown in Table 3.

### C. SDN-SlowRate-DDoS 數據集 (Dataset)  
> Using the data center testbed, a set of experiments was performed to capture a dataset. Table 4 shows the set of experiments included in the SDN-SlowRate-DDoS dataset. In total, 23 experiments were executed, varying different parameters such as the number of attackers (A), number of victims (V), duration of the experiment (T), and attack rate (r). For all experiments, the number of attack connections C was set to 20000 connections. The slow http read attack was selected because it is one of the most harmful slow-rate DDoS attacks [25]. For all experiments with T = 4000, legitimate traffic starts at t = 0 s and ends at t = 4000 s, while attacks are executed from t = 1000 to t = 3200 s. In the case of experiments with T = 1200 s, legitimate traffic starts and ends at t = 0 and t = 1200 s, respectively, while attack traffic is limited to t = 300 to t = 900 s. Note that for A = 0 and V = 0, only legitimate traffic is generated in the network.  
> The SDN-SlowRate-DDoS dataset offers two components: (i) pcap files captured at the mirroring switch (see VS5 in Figure 4), and (ii) comma separated value (CSV) files containing ONOS statistics of the network flows. As the pcap files are captured at the mirroring switch, they contain all traffic from the network. Researchers interested in evaluating machine learning (ML) or DL models to detect slow-rate DDoS attacks can use applications such as CICFlowMeter, Tshark, NetMate, or ARGUS [26] to capture network flows from these pcap files and train and evaluate their models.  
> On the contrary, researchers interested in evaluating ML or DL models using centralized monitoring systems based on controller statistics can use the features presented in the CSV files. Table 5 shows the features of the network flows included in the CSV files. The sampling time for these statistics is 1 second.  
> According to Table 5, each sample contains 13 columns. Nine of these features identify a specific network flow: DeviceID (identification of the SDN switch), FlowId, IpSrc, IpDst, MacSrc, MacDst, PortSrc, PortDst, and Protocol. Furthermore, three relevant flow characteristics are captured, including the number of bytes and packets processed by the flow and the life time of the flow. An additional feature named TimeStamp is provided, which represents the time the flow was sampled. Raw statistics presented in Table 5 can be used to calculate other relevant flow statistics, such as median bytes per flow, median packets per flow, median duration of flow, etc, as presented in [27]. These SDN controller-based statistics are valuable for designing, testing, and evaluating DDoS detection systems using ML or DL.  
> Finally, note that CSV files are provided for all experiments in Table 4. However, not all experiments contain the pcap files, mainly because our memory limitation during the creation of the dataset. The total size of the dataset is 388 GB.

### D. IDS性能評估 (IDS Assessment)  
> In this study, the long short-term memory (LSTM) model presented in [10], which was trained using data captured from a simulated datacenter, is used to classify attack and legitimate traffic in the SN4I-based testbed. The data center network topology used to train and evaluate the LTSM model in [10] is similar to the physical network topology used in this study. Therefore, as this model demonstrated high performance and robustness to detect slow-rate DDoS attacks in simulated conditions (it showed an average detection rate of 98% in [10]), in this work the LSTM model’s performance was considered to be validated in real conditions with physical equipment. Furthermore, it is worth noticing that the tool (Slowhttptest) used to generate attack traffic in [10] is also the one employed in this study. Nevertheless, in this work legitimate traffic is generated differently from that in [10]. Particularly, traffic of FTP and video streaming is new for the LSTM model.  
> Table 6 shows the mean values of accuracy and FPR for various experiments that combine different numbers of attackers A and victims V. As the LSTM model was trained with legitimate traffic different from that used for its evaluation, a high level of FPRs is observed. In particular, it was observed that FTP and video streaming traffic caused most false positive events. However, these results are relevant given that the evaluation is performed in a production environment. Previous studies, including our study in [9], demonstrated that ML or DL models can achieve high performance, but most of them were evaluated using datasets or simulated environments.

### E. IPS性能評估 (IPS Assessment)  
> Table 7 shows the experiments carried out to evaluate the performance of the IPS. The number of attackers A, the number of victims V, the attack rate r, and the duration of the experiment T are varied to obtain a set of 13 experiments. For all experiments, the number of attack connections is set to C = 20000.  
> Figure 6 shows an example of the behavior of the IPS for an experiment that involves four attackers (A = 4) and one victim (A = 1). From top to bottom, the four first images show the IPS’ actions for the malicious connections, while the last image shows the IPS’ actions for one legitimate connection. It is observed that the first three attackers are correctly blocked. In the case of the fourth attacker, it was initially temporarily blocked and recovered. However, as it still continues to attack the server, it is detected by the IDS and the IPS blocks the attacker permanently.  
> Figure 7 shows the traffic (packets/second) for the sample experiment described above. The traffic behavior of one legitimate connection is shown in green, whereas the traffic behaviors of the four attack connections are shown in other colors, rather than green. The top image of Figure 7 presents the traffic for the selected connections (four attack connections and one legitimate connection) when the IPS is not activated, while the bottom image depicts the traffic when the IPS is activated. The attacks start at t = 300 s and end at t = 900 s. When IPS is deactivated, attack connections are observed to use most of the network resources, leading to a denial of service to legitimate users. However, when IPS is activated, the attack traffic is blocked and legitimate connections are minimally affected by malicious packets injected by attackers before they are detected and blocked.  
> According to the IPS design, a connection can be temporarily or permanently blocked depending on how critical the attack is. An effectiveness of 100% of the IPS means that all attack connections are immediately and permanently blocked. Nevertheless, the closed loop of traffic monitoring, attack detection and mitigation requires a minimal execution time. Furthermore, even if the attack connections are temporarily blocked, it certainly helps the system’s performance. In this regard, two metrics are presented in Figure 8 (for all malicious connections and for all experiments presented in Table 7): (i) the mean response time for attacks that are permanently blocked, and (ii) the mean response time for attackers that are temporarily or permanently blocked. It is observed that the former is always lower than the latter. This condition indicates that most of the time the IPS first considers malicious connections as noncritical. However, as they continue to attack the servers, they are identified as critical connections and thus permanently blocked by the IPS.  
> There is no a clear trend of the response time when the number of attackers A and victims V is varied. Furthermore, the mean response time, considering all experiments, for permanently blocking attack connections is 65.95 s, while the mean response time for either temporarily or permanently blocking attack connections is 53.18 s.  
> Figure 9 depicts the efficiency of the IPS to mitigate slow-rate DDoS attacks. IPS demonstrates 100% of effectiveness in mitigating malicious connections (permanently + temporarily blocking attack connections) for A = 1 and V = 1, A = 4 and V = 1, A = 3 and V = 3. For A = 4 and V = 2, the IPS’s mitigation performance is reduced to 91.66%. Furthermore, the IPS is able to permanently mitigate more than the 75% of the connections for all conditions of A and V.  
> Finally, Figure 10 shows the mean number of legitimate connections blocked by the IPS. An ideal IPS does not block legitimate connections. However, given that IDSs tend to produce false positives, there is a probability that the IPS blocks legitimate connections.  
> According to Figure 10, the IPS affects on average less than one legitimate connection for all experiments. However, blocking even a single connection is critical in production environments. In this sense, the IPS included Recovery actions when a connection is temporarily or permanently blocked, as shown in Figures 2 and 3. Therefore, the IPS releases the negligible number of legitimate blocked connections, and they are minimally interrupted.

* *重要發現**：  
- LSTM模型在真實環境中仍具高檢測能力，但因合法流量差異導致較高誤報率(FPR約13.23%)。  
- IPS能有效阻斷攻擊連接，平均響應時間約53秒，且大多數攻擊最終被永久封鎖。  
- IPS對合法連接影響極小，平均封鎖少於一個合法連接，且具恢復機制減少誤封影響。

- --

## V. 討論 (Discussion)  
* *位置**：頁面46828起始  

### A. 框架性能 (Framework Performance)  
> The LSTM model presented a high performance to detect slow-rate DDoS attacks in a real scenario, even if the data used to train this model are based on simulation [10]. In particular, the legitimate simulated traffic used to train the DL model differed significantly from that of the physical testbed used in this study to test the model. This condition resulted in a mean value of the FPR of 13.23%. One solution to increase the performance of the LSTM model is to retrain it with the traffic collected from the physical testbed. This approach is considered for future work.  
> Furthermore, even if the DL model did not perfectly separate the attack from legitimate connections, the IPS was totally capable of performing the correct mitigation actions. It timely blocked slow-rate DDoS attacks in mean time <53.18 s. Similar work presented in [28] and [29] demonstrated an average mitigation time of less than 30 s for low-rate DDoS attacks. However, they used simulated testbeds, small topology, and their tests were limited to A = 1 and V = 1. Consequently, the migration of their solutions to networks with physical equipment will certainly increase their IPSs’ response times.  
> The IPS’ mean response time presented in this work (53.18 s) using physical equipment is more than two times the response time obtained in simulations in our previous study in [10], where the IPS’ average response time was lower than 20 s for A = 4 and V = 1. This increase in response time was expected since, unlike the simulated testbed presented in [10], in this work the IDS, IPS, and ONOS controller are placed in physically separated computers interconnected by a router, as presented in Figure 4, which delays the execution of mitigation actions. Nevertheless, this response time is small enough to successfully mitigate the slow-rate DDoS attacks. On top of that, this difference in response times of simulated versus real conditions highlights the importance of validating the design of a security system in production networks in order to ensure that it is effective and scalable.  
> Finally, the solution proposed in this work did not affect legitimate connections, since the mean number of legitimate connections blocked is less than one. This result is relevant since regardless of whether the IDS presented a high FPR, the IPS was effective in blocking only critical connections.

### B. 慢速率DDoS數據集 (Slow-Rate DDoS Dataset)  
> The design of an effective security solution is highly dependent on the dataset used to test them. The dataset provided contains data generated with real equipment from the SN4I infrastructure.  
> Unlike previous security datasets, the two resources provided in our dataset allow interested researchers to design and test three types of IDS: (i) network packet statistics-based IDSs, (ii) flow statistics-based (e.g. CICFlowMeter statistics) IDSs, and (iii) controller statistics-based IDSs.

- --

## VI. 結論與未來展望 (Conclusion and Future Work)  
* *位置**：頁面46829起始  

> This work presented the evaluation of an automated security framework using real equipment. The results of the detection and mitigation of DDoS attacks showed the high effectiveness of the solution. Additionally, the SDN-SlowRate-DDoS dataset was introduced that collects real traffic with slow-rate DDoS attack events. This dataset will help researchers design and test realistic IDSs.  
> Furthermore, the proposed framework uses a monitoring switch that captures all traffic from the network, which could limit the scalability of the solution. Future work considers improving the monitor module by using P4-enabled switches that monitor, filter, and process packets before they are sent to the Monitor module, which will increase the scalability of the framework.  
> Finally, the results of the proposed framework evaluated in a real scenario indicate that using intelligent mechanisms, it is possible to effectively automate the mitigation of complex DDoS attacks. This work used DL to detect attacks. Using intelligent and adaptive mitigation mechanisms will improve the proposed framework. Therefore, in future work, reinforcement learning-based solutions for DDoS mitigation will be tested using the physical testbed.

* *重要結論與未來方向**：  
- 實驗證明基於SDN的自動化框架在真實環境中有效檢測與緩解慢速率DDoS攻擊。  
- 發布的SDN-SlowRate-DDoS數據集為設計現實IDS提供重要資源。  
- 未來將提升監控模組的可擴展性，考慮使用P4可編程交換機。  
- 計劃引入強化學習等智能自適應緩解機制，進一步提升系統性能。

- --

# 附錄：數學公式說明  
- **mstate計算公式**：  
$$
mstate_{i,j} = \frac{1}{1 + e^{-(g_{i,j} - \eta)}}
$$  
其中，  
$$
g_{i,j} = \sum f_{i,j}
$$  
$f_{i,j}$為在時間區間內對連接$i,j$的攻擊檢測事件（1為檢測到攻擊，0為未檢測）。$\eta$為閾值參數，用於調節攻擊嚴重度的判定。此公式為sigmoid函數，將攻擊檢測次數映射為0至1之間的概率值，作為連接的攻擊嚴重度指標。

- --

以上為該論文的完整關鍵章節內容提取，包含原文引用、重要數據、公式及技術說明，方便讀者深入理解研究內容與成果。

---

> **注意**：本文檔包含數學公式，請使用支持LaTeX數學渲染的Markdown查看器（如VS Code + Markdown Math插件、Typora、JupyterLab等）以獲得最佳顯示效果。