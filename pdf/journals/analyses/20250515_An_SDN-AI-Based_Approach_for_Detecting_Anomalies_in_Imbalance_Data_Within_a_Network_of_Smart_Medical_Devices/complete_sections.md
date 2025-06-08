# An_SDN-AI-Based_Approach_for_Detecting_Anomalies_in_Imbalance_Data_Within_a_Network_of_Smart_Medical_Devices.pdf 完整關鍵章節

## 摘要 (Abstract)  
* *位置**：論文開頭

> The Internet of Medical Things (IoMT) has become a novel paradigm for real-time healthcare applications. Artificial intelligence (AI) based efforts have been made to address the security challenges of IoMT, the problem of imbalance data still exists, due to which AI algorithms cannot sufficiently learn malicious traffic behavior and fail to identify rare anomalies in imbalance data accurately. Therefore, in this article, we propose an intelligent model based on software defined networking and deep learning (DL) to handle the heterogeneous, complex, and distributed architecture. To tackle the imbalance challenge, the proposed model utilizes generative adversarial network (GAN) to generate plausible synthetic data for minor class traffic. It combines autoencoder-driven DL models with reconstruction error and Wasserstein distance-based GAN. When compared to naive and advanced techniques, the proposed model produced noticeably better results on an imbalance dataset and outperformed these techniques by 4.78% and 4.54% in terms of accuracy and F1-score values, respectively.

* *重要發現**：  
- 提出結合SDN與深度學習的智能模型來處理IoMT中異質、複雜且分散的架構。  
- 利用GAN生成少數類別的合成數據以解決資料不平衡問題。  
- 模型在不平衡資料集上相較於基線方法提升約4.78%準確率與4.54% F1分數。

- --

## 引言 (Introduction)  
* *位置**：摘要後，正文第一段開始

> & INTERNET OF MEDICAL Things (IoMT) is frequently used to refer to the Internet of Things (IoT) as it relates to health applications. By 2022, the global value of this industry is expected to surpass US$158 billion, with linked medical devices directly responsible for about one-third of this expense. The diagnosis, tracking, and treatment of chronic illnesses such as diabetes, dementia, Parkinson’s disease, epilepsy, seizure disorders, and sleep disorders are important uses for the IoMT. However, due to its complex, distributed, heterogeneous, and dynamic nature, IoMT devices are incompatible with traditional network infrastructure resulting in inefficient resource utilization. Another challenge associated with the IoMT is the accurate detection of anomalies from imbalanced data. Most of the collected data comprises normal flows, with rare malicious behaviors capable of causing service failure. Within this category, specific types of attacks are exceptionally rare. As the frequency, sophistication, and complexity of cyberattacks increase, this imbalance of data between normal and malicious behaviors presents a significant hurdle for most artificial intelligence (AI) models. Their struggle lies in effectively securing systems due to the difficulty in learning and recognizing these rare anomalies. This article aims to tackle the aforementioned challenges of IoMT by proposing an architecture based on software defined network (SDN) and deep learning (DL), where SDN can effectively manage the heterogeneity, complexity, and distributed nature of the IoMT and imbalance data challenge in SDN-IoMT is addressed by employing the generative adversarial network (GAN). The main contributions of this work are as follows.  
> 1. The proposed model employed SDN and generative adversarial network-autoencoder (GAN-AE) to accurately detect anomalies within imbalance data in a network of smart medical devices.  
> 2. The performance of the proposed GAN-AE model is compared with baseline (LSTM) and advanced (CNNAE) techniques to evaluate the proposed model thoroughly. All models have been trained and evaluated in the same setting to ensure a fair comparison.  
> 3. The proposed model undergoes testing and evaluation within a simulated environment using the SDN-IoMT imbalance dataset. The evaluation employs a tenfold cross-validation technique to demonstrate balanced results.

* *重要主張**：  
- IoMT因其複雜且分散的特性，傳統網路架構難以有效支援。  
- 資料不平衡問題嚴重影響AI模型對罕見攻擊的識別能力。  
- 本文提出結合SDN與GAN-AE的深度學習模型，專門針對不平衡資料中的異常檢測。  
- 透過與LSTM及CNNAE模型的比較，證明所提模型的優越性。  
- 使用十折交叉驗證確保評估結果的穩健性。

- --

## 文獻綜述 (Related Work)  
* *位置**：引言後

> In the literature, efforts have been made to address the challenge of anomaly detection and prevention in IoMT by employing SDN and AI-based techniques. Wagan et al. combined two DL methods to perform IoMT anomaly detection. According to the performance assessment, it achieved individual accuracy of 92.95% and multimodal joint accuracy of 89.67%. In Zachos et al. the proposed AIDS depends on machine learning approaches to detect irregularities in the IoMT data taking into account the computing overhead. Radoglou-Grammatikis et al. addressed cybersecurity challenges in healthcare, specifically focusing on the IEC 60870-5-104 protocol. In Huang et al. a hotel anti-epidemic management system was proposed to disinfect the used rooms by using UV LEDs through WiFi communication with the front desk computer and, therefore, it can protect quests from virus infection. Alazab et al. presented an overview and recent advances of digital twins for healthcare 4.0. An architecture of digital twins for healthcare is also proposed. Furthermore, they presented several use cases of digital twins. Adil et al. presented a detailed survey of healthcare IoT applications in the context of AI-enabled EEC technology to identify unresolved security challenges that need attention from the research community and healthcare stakeholders and then suggest potential research directions to give a clear future insight.  
> The literature review highlights that no existing work has been found that specifically addresses the smart healthcare imbalance data for detecting minor class attacks. To the best of our knowledge, this article represents the first attempt to detect minor class attacks and anomalies by applying SDN and AI.

* *重要發現**：  
- 現有研究多聚焦於IoMT異常檢測，使用多種DL與機器學習方法，準確率約在90%以上。  
- 目前尚無研究專門針對智能醫療中不平衡資料的少數類別攻擊檢測。  
- 本文為首個結合SDN與AI針對少數類別攻擊檢測的嘗試。

- --

## 研究方法 (Proposed Methodology)  
* *位置**：文獻綜述後

### 系統架構  
> The imbalance data in the IoMT environment make it extremely difficult to precisely identify and categorize anomalies and cutting-edge attacks. Medical data is one area where this problem is especially common. This problem exists mainly because many AI and DL models have biases that make them prefer the majority classes and make it difficult to detect minor class abnormalities. To address this problem, we have proposed a multilayered architecture consisting of a sensing layer, data and control layer, and application layer. The schematic diagram of the proposed method is presented in Figure 1. The sensing layer includes a range of IoMT devices, including actuators and medical sensors. These sensors are used for detecting blood pressure, temperature, and heart rate. This layer is primarily responsible for collecting and forwarding data to the next layer. The data layer is the second layer in the proposed model, and it includes various networking hardware such as switches and routers that support SDN. This layer is critical in enabling the seamless transfer of data across switches. The control layer is the system’s primary control hub. Within this layer, the SDN controller has a global view of the entire network and manages various aspects, such as effectively managing congestion, optimizing routing, ensuring Quality of Service, and augmenting security measures. To detect and classify abnormalities in the imbalance dataset, we integrated the GAN-AE DL model into the SDN controller in our framework.

### 資料前處理 (Data Preprocessing)  
> Raw data have been prepared and cleaned so that it can be used by DL algorithms. The dataset is processed using a variety of methods. Lines containing nonnumeric characters or empty values are initially removed to ensure that their impact on the performance of the test model is minimal. Because DL algorithms perform best with numerical data, nonnumerical values are converted to numerical equivalents using the label encoder, specifically sklearn. Furthermore, because the order of segments could affect model performance unexpectedly, the output label is encoded once. Data standardization is performed using the MinMax scalar function to improve the model performance.

### 合成資料生成 (Synthetic Data Generation With GAN)  
> Using the refined dataset, the generative model is constructed and trained using the synthetic data generation module. The generative model we employed is called boundary equilibrium generative adversarial network (BEGAN), and it functions similarly to the AE. We constructed the generator using the same architecture as the discriminator’s decoder and the discriminator itself as a symmetric five-layer AE model. The system first divides the provided dataset into classes before creating generative models for each divided subdataset, which is then used to train the BEGAN model. In other words, generative models are constructed in an equal number as classes, and each generative model only generates synthetic data that corresponds to a specific class after training. Establishing the criterion for terminating the training process is critical to using the BEGAN model for minor class anomalies detection. This decision has a significant impact on the effectiveness of anomaly detection because it is directly related to the synthetic data used to train the detection model. The ability of BEGAN to estimate training convergence using the equilibrium concept distinguishes it from other GAN models. The following is the BEGAN convergence formula:  
>  
> $$C:M = \mathcal{L}(a) + |a \mathcal{L}(a) - \mathcal{L}(G(z))|$$  
>  
> The term $\mathcal{L}(\cdot)$ represents the reconstruction error function in (1), while $a$ represents the diversity ratio for a specific dataset class.  
> The convergence measure (M) is used to terminate the training phase of a generative model. The system input parameter is treated as a threshold value throughout training, and the training process is terminated if the convergence measure (M) falls below the designated threshold. We set the (M) threshold value at 0.058 in our proposed paradigm. Following generative model training, the system employs the trained generator to generate synthetic data based on the classes. After that, the generated synthetic dataset is combined with the real training data. In the following steps, both the AE and the detection model are trained on the expanded dataset. Originally designed to generate generative models for each class, the synthetic data generation module can also be designed as a single model, embedding class attributes within the input space by leveraging the conditional GAN architecture.

### 自編碼器訓練 (AE Training)  
> The AE model is first trained to carry out dimension reduction and feature extraction procedures in order to build an effective anomaly detection model. The generative model discriminator’s design and the AE architecture in our proposed model are the same. An AE model is constructed, trained on the expanded dataset, and then the trained encoder is applied to the feature extraction process. Algorithm 1 represents AE’s entire training procedure. It is noteworthy that the input layer of the detection models is the trained encoder, which is placed first. It is set up only to be a feature extractor and is set not to learn anymore when training detection models.

* *Algorithm 1. Training of Autoencoder with generators**```
1: INPUT : Training DataSet (TD) TDtrain and set of generators G
2: Initialization of AE parameters m0_AE
3: for Gi ∈ G, where 1 ≤ i ≤ k do
4:    z = {z_j} for j = 1, 2, ..., m_i
5:    Synthetic DataSet (SD) = Gi(z)
6: end for
7: Expanded Dataset (ED) = TDtrain ∪ SD1 ∪ ... ∪ SDk
8: mAE = TrainAE(m0_AE; ED)
9: mE = Encoder(mAE)
10: OUTPUT: Trained Encoder (mE)
```

### 預測模型訓練 (Predictive Model Training)  
> At this point, we used deep neural network (DNN), convolutional neural network (CNN), and long short term memory (LSTM) algorithms to categorize abnormalities. Due to its inherent features, our DNN model, which has two hidden layers, performed well in identifying anomalies using the supplied fine-tuned datasets. CNN is the second classifier, and it was created mainly to analyze picture datasets. To make it suitable for IoMT imbalance data classification in terms of layers and input data space, a few structural modifications are needed. Hence, rather than transforming the input data into 2-D space, the CNN is built utilizing one-dimensional (1-D) convolutional layers for the classification of the IoMT imbalance dataset. Consequently, the CNN model is comprised of one fully connected layer and two 1-D convolutional layers. LSTM is the third classification of the DL model. It consists of two recurrent layers with LSTM units and a fully connected layer. For the analysis of temporally linked characteristics, LSTM is especially helpful. The output layer of all DL models has multi-valued fields when the goal is to identify anomalies. Using the trained generators and encoder, Algorithm 2 describes the comprehensive method for training the predictive model. To put it briefly, the training of the detection model comes first, followed by data preparation, before the anomaly detection and classification model operates. We use G-CNNAE to describe our model. In addition, we have categorized the predictive models into three groups for a thorough comparison:  
> - LSTM, which is referred to as the naive DL model.  
> - CNNAE, which is model combined with AE and is called an advanced DL model.  
> - G-CNNAE, which is the proposed model.  
> In the application layer, security and medical experts analyze the current situation and take the necessary and appropriate actions.**Algorithm 2. Generators-based classifier training**```
1: INPUT : Training DataSet (TD) TDtrain, set of generators G, and Trained Encoder (mE)
2: Initialization of classifier parameters x0
3: for Gi ∈ G, where 1 ≤ i ≤ k do
4:    z = {z_j} for j = 1, 2, ..., m_i
5:    Synthetic DataSet (SD) = Gi(z)
6: end for
7: Expanded Dataset (ED) = TDtrain ∪ SD1 ∪ ... ∪ SDk
8: Trainable state of mE is set to false
9: Build x0_mE = Model-Concatenation(mAE; x0)
10: xmE = Train-Classifier(x0_mE; ED)
11: OUTPUT: Trained Encoder (xmE)
```**重要說明**：  
- GAN使用BEGAN架構，透過平衡收斂指標$M$（設定閾值0.058）判斷訓練終止。  
- AE用於特徵萃取，訓練後凍結權重作為特徵提取器。  
- 預測模型包含DNN、1D-CNN與LSTM三種架構，分別代表不同複雜度的模型。  
- G-CNNAE為本文提出的結合GAN生成資料與CNNAE的模型。

- --

## 實驗設置與評估指標 (Experimental Setup and Evaluation Metrics)  
* *位置**：研究方法後

> The proposed model is implemented in the SDN-IoMT environment with the Mininet 2.3.0 simulation tool. Then, a DL model using the TensorFlow framework is employed inside the ONOS SDN controller. TensorFlow v2.12.0, the most recent version, is installed in the setup. A laptop equipped with an eighth generation Intel Core i9 processor, 16 GB of RAM, and a 1 TB hard drive is used to run the simulations.  
>  
> Hyperparameters and Implementation:  
> The GAN discriminator is designed with three layers. The first hidden layer comprises 80 neurons along with 50 latent space dimensions. Consequently, the generator’s hidden layer also includes 80 neurons with a 50-D latent space. The activation function employed is ReLU. It is noteworthy that the AE functions as a feature extractor, and its architecture mirrors that of the discriminator. Moreover, we established the threshold for the convergence of GAN at 0.058. The process to train the model halts if it falls below this threshold or when epochs reach 280. Similarly, the AE training concludes after 300 epochs. For classification, we have selected three models: DNN, CNN, and LSTM, each configured with two hidden layers. In the DNN, the one-layer contains 32 neurons, and the second has 16 neurons. Our CNN employs a 1-D-CNN architecture with two convolutional layers. The first layer is equipped with 32 convolutional filters, while the second layer functions as a fully connected layer with 16 neurons. ReLU is utilized as the activation function within the CNN. The last model we used for classification is LSTM, where each layer consists of 64 connected LSTM cells. In addition, we concatenated a fully connected layer with 32 neurons to the LSTM.  
>  
> After a thorough examination of the literature, it is clear that no publicly dataset is currently available related to SDN-based smart medical devices to analyze and assess the efficiency of the proposed technique. There is just one dataset available for SDN-IoT environments in the literature, and it is mostly focused on network traffic intrusion detection. Furthermore, there is just one dataset available for the Internet of Healthcare Things (IoHT) known as ECU-IoHT; however, this dataset did not take SDN integration into account and instead focused solely on the IoT-Healthcare domain. Through an extensive literature review, it is found that both datasets mentioned above are not imbalance datasets.  
>  
> Considering the proposed model, we undertook the simulation and development of an SDN-IoMT imbalance dataset that leverages both Sarica and Angin and Ahmed et al. techniques. To achieve this, three types of smart medical sensors are simulated within an SDN-based environment: a temperature sensor, a blood pressure sensor, and a heart rate sensor. The temperature sensor generates data every 10 seconds, while the blood pressure sensor produces a large volume of values primarily useful for attack detection. Meanwhile, the heart rate sensor generates data more frequently compared to the first two sensors. In line with the approach outlined in Sarica and Angin, a similar topology and packet sending rate for normal traffic are used. The generation and recording of this normal traffic executed both with and without the presence of malicious traffic. Four types of attacks are conducted—Nmap port scan, ARP poisoning, DoS attack, and Smurf attack—to assess the robustness of the proposed technique. Dataset consists of 57,895 instances, and each instance comprises 18 attributes. The SDN-IoMT dataset is highly imbalanced, with three out of five classes (ARP Spoofing, Nmap PortScan, Smurf Attack) comprising less than 10% of the overall training data. With a weight of 0.53%, the Smurf Attack class has the lowest weight. This imbalance has a major effect on how the proposed model is trained. In addition, simulations are performed in an SDN-based environment during the dataset’s creation process. A comparison between the imbalance SDN-IoMT dataset and state-of-the-art existing datasets is presented in Table 1.  
>  
> As part of our methodology, we divided the dataset into training and testing sets, allocating 70% for training and 30% for testing purposes. The distribution of the dataset is detailed in Table 2. The evaluation of the proposed technique is conducted using four standard metrics: accuracy, precision, recall, and F1-score.

* *表格摘要**：

| 表1. SDN-IoMT資料集與現有資料集比較 | Imbalance | SDN | IoMT |
|------------------------------------|-----------|-----|------|
| Ref. 13                           | No        | Yes | No   |
| Ref. 14                           | No        | No  | Yes  |
| Ref. 15                           | Yes       | No  | No   |
| SDN-IoMT (本研究)                 | Yes       | Yes | Yes  |

| 表2. SDN-IoMT不平衡資料集分布 | 類別          | 訓練數量 | 訓練權重% | 測試數量 | 測試權重% |
|------------------------------|-------------|---------|----------|---------|----------|
| Normal                       | 33,637      | 83%     | 13,894  | 80%     |
| DoS Attack                  | 4,458       | 11%     | 1,476   | 8.5%    |
| ARP Spoofing                | 1,366       | 3.37%   | 1,077   | 6.2%    |
| Nmap PortScan              | 851         | 2.1%    | 677     | 3.9%    |
| Smurf Attack               | 215         | 0.53%   | 243     | 1.4%    |
| **Total**| 40,527      | 100%    | 17,368  | 100%    |**重要說明**：  
- 自行模擬SDN-IoMT不平衡資料集，包含正常流量與四種攻擊類型。  
- Smurf攻擊類別極少（0.53%），為少數類別檢測的挑戰。  
- 使用70%訓練、30%測試分割。  
- 評估指標包含準確率、精確率、召回率與F1分數。

- --

## 結果分析與討論 (Results and Discussion)  
* *位置**：實驗設置後

> In this section, the achieved results are discussed. It is important to note that the utilized SDN-IoMT dataset exhibits an imbalance, particularly within its minor and major classes. To enhance the classification accuracy, the proposed model generates synthetic data for minor classes based on their weights within the overall dataset. In experimentation, synthetic data are exclusively generated for those minor classes constituting less than 10% of the total distribution. Consequently, 5000 synthetic data points are generated for each of the following classes: ARP Spoofing, Nmap PortScan, and Smurf Attack, utilizing a trained GAN model.  
> The proposed model utilized a tenfold cross-validation technique, and the results are presented in Table 3. Each fold’s results are meticulously displayed, providing a comprehensive understanding. The performance of the proposed model is evaluated on a test dataset using a confusion matrix, depicted in Figure 2. The clarity of the confusion matrix illustrates the proposed model’s precise and efficient classification across all five classes, notably the minor ones. The comparison between the proposed model and the baseline DL models based on accuracy, recall, precision, and F1-score is presented in Figure 3.  
> The proposed model achieved the highest accuracy and precision values of 94.44% and 99.32%, respectively. Furthermore, the recall and F1-score values of the proposed model are 99.35% and 93.34%, respectively. The results indicate that the proposed technique has outperformed both the naive and advanced baseline DL models. The accuracy and F1-score values for each class are detailed in Table 4. The proposed model outperformed the naive LSTM and advanced (CNNAE) DL models by 4.78% and 4.54% in terms of accuracy and F1-score values, specifically on the extremely minor class (Smurf Attack), which accounts for only 0.53% of the overall dataset. This indicates a significant 4–5% improvement by the proposed model on the extremely minor class. In addition, the proposed model exhibited an 8–10% better result compared to competitors on normal classes and major classes such as DoS and ARP. While the proposed model holds potential for enhancing classification performance, there is still the challenge of relatively low detection rates across certain classes. In particular, the proposed model observed to have relatively low detection rates for the Smurf class. Moreover, the proposed model is computationally expensive to some extent because the SDN controller and AI models demand certain level of computational resources.

* *表3. 十折交叉驗證結果摘要**| 指標       | 模型    | 1    | 2    | ... | 10   |
|------------|---------|------|------|-----|------|
| Accuracy % | LSTM    | 83.70| 83.56| ... | 83.33|
|            | CNNAE   | 89.63| 89.23| ... | 89.88|
|            | G:CNNAE | 94.21| 94.18| ... | 94.54|
| Recall %   | LSTM    | 98.89| 98.25| ... | 98.35|
|            | CNNAE   | 98.59| 98.52| ... | 98.16|
|            | G:CNNAE | 99.32| 99.16| ... | 99.34|
| Precision %| LSTM    | 72.18| 73.05| ... | 73.29|
|            | CNNAE   | 80.10| 81.25| ... | 81.65|
|            | G:CNNAE | 86.40| 86.65| ... | 86.91|
| F1-Score % | LSTM    | 83.20| 83.72| ... | 83.89|
|            | CNNAE   | 88.69| 88.51| ... | 88.71|
|            | G:CNNAE | 93.20| 93.28| ... | 93.69|**表4. 各類別準確率與F1分數比較**| 類別       | LSTM Accuracy % | CNNAE Accuracy % | G:CNNAE Accuracy % | LSTM F1 % | CNNAE F1 % | G:CNNAE F1 % |
|------------|-----------------|------------------|--------------------|-----------|------------|--------------|
| Normal     | 83.70           | 90.67            | 94.14              | 82.42     | 85.79      | 92.97        |
| DoS        | 84.63           | 89.90            | 94.23              | 84.95     | 89.26      | 94.90        |
| ARP        | 83.89           | 90.32            | 93.33              | 45.88     | 81.34      | 91.43        |
| Nmap       | 83.78           | 89.23            | 94.98              | 12.76     | 16.56      | 23.78        |
| Smurf      | 84.63           | 89.66            | 94.90              | 10.34     | 15.67      | 22.89        |**重要發現**：  
- 針對少數類別（如Smurf攻擊）生成5000筆合成資料，顯著提升模型識別能力。  
- G-CNNAE模型在整體準確率、精確率、召回率及F1分數均優於LSTM與CNNAE。  
- 對極少數類別的準確率提升約4.78%，F1分數提升約4.54%。  
- 模型在部分類別（如Smurf）仍有較低檢測率，且計算資源需求較高。

- --

## 結論 (Conclusion)  
* *位置**：結果討論後

> In this article, we proposed a SDN and DL-based framework for anomaly and attack detection in an environment where a network of smart IoMT devices collects a huge amount of imbalance data. Specifically, the SDN architecture is integrated with an IoMT network to handle its complex, heterogeneous, and distributed architecture. Subsequently, a DL model based on GAN-AE is deployed at the control plane to improve the detection mechanism for minor class attacks and anomalies. The effectiveness of the proposed model is demonstrated in terms of accuracy, precision, and F1-score through experimental evaluation on an SDN-IoMT imbalance dataset. In addition, the performance of the proposed model is compared against both naive and advanced DL techniques. In the future, the aim is to train the model on different imbalance datasets to further enhance the detection of minor class attacks in a network of various fields of life.

* *重要結論**：  
- 成功提出結合SDN與GAN-AE的深度學習框架，有效提升IoMT中不平衡資料的異常檢測能力。  
- 實驗證明該模型在準確率、精確率及F1分數上均優於現有基線模型。  
- 未來計畫擴展至其他不平衡資料集與不同領域的少數類別攻擊檢測。

- --

## 參考文獻 (References)  
* *位置**：論文末尾

> 1. Y. A. Qadri, A. Nauman, Y. B. Zikria, A. V. Vasilakos, and S. W. Kim, “The future of healthcare Internet of Things: A survey of emerging technologies,” IEEE Commun. Surv. Tut., vol. 22, no. 2, pp. 1121–1167, Second Quarter 2020.  
> 2. S. Baker and W. Xiang, “Artificial intelligence of things for smarter healthcare: A survey of advancements, challenges, and opportunities,” IEEE Commun. Surv. Tut., vol. 25, no. 2, pp. 1261–1293, Second Quarter 2023.  
> 3. L. N. Tidjon, M. Frappier, and A. Mammar, “Intrusion detection systems: A cross-domain overview,” IEEE Commun. Surv. Tut., vol. 21, no. 4, pp. 3639–3681, Fourth Quarter 2019.  
> 4. S. A. Wagan et al., “A fuzzy-based duo-secure multi-modal framework for IoMT anomaly detection,” J. King Saud Univ.-Comput. Inf. Sci., vol. 35, no. 1, pp. 131–144, 2023.  
> 5. G. Zachos et al., “An anomaly-based intrusion detection system for Internet of medical things networks,” Electronics, vol. 10, no. 21, 2021, Art. no. 2562.  
> 6. P. Radoglou-Grammatikis et al., “Modeling, detecting, and mitigating threats against industrial healthcare systems: A combined software defined networking and reinforcement learning approach,” IEEE Trans. Ind. Inform., vol. 18, no. 3, pp. 2041–2052, Mar. 2022.  
> 7. K.-C. Huang et al., “Consumer systems for healthcare and wellbeing,” Jul. 2022, doi: 10.1109/ICCE-Taiwan55306.2022.9869075.  
> 8. M. Alazab et al., “Digital twins for healthcare 4.0–Recent advances, architecture, and open challenges,” IEEE Consum. Electron. Mag., vol. 12, no. 6, pp. 29–37, Nov. 2023.  
> 9. M. Adil et al., “AI-driven EEC for healthcare IoT: Security challenges and future research directions,” IEEE Consum. Electron. Mag., vol. 13, no. 1, pp. 39–47, Jan. 2024.  
> 10. D. Berthelot, T. Schumm, and L. Metz, “Began: Boundary equilibrium generative adversarial networks,” 2017, arXiv:1703.10717.  
> 11. B. Lantz, B. Heller, and N. McKeown, “A network in a laptop: Rapid prototyping for software-defined networks,” in Proc. 9th ACM SIGCOMM Workshop Hot Topics Netw., 2010, pp. 1–6.  
> 12. F. De Keersmaeker et al., “A survey of public IoT datasets for network security research,” IEEE Commun. Surv. Tut., vol. 25, no. 3, pp. 1808–1840, Third Quarter 2023.  
> 13. A. K. Sarica and P. Angin, “A novel SDN dataset for intrusion detection in IoT networks,” in Proc. 16th Int. Conf. Netw. Serv. Manage., 2020, pp. 1–5.  
> 14. M. Ahmed et al., “ECU-IoHT: A dataset for analyzing cyberattacks in Internet of Health Things,” Ad Hoc Netw., vol. 122, 2021, Art. no. 102621.  
> 15. M. Tavallaee et al., “A detailed analysis of the KDD CUP 99 data set,” in Proc. IEEE Symp. Comput. Intell. Secur. Defense Appl., 2009, pp. 1–6.

- --

以上為該論文的完整關鍵章節內容提取，包含所有重要數據、公式、演算法及實驗結果，並以Markdown格式呈現，確保數學公式與技術細節的準確性與可讀性。

---

> **注意**：本文檔包含數學公式，請使用支持LaTeX數學渲染的Markdown查看器（如VS Code + Markdown Math插件、Typora、JupyterLab等）以獲得最佳顯示效果。