# Explainable_AI_Feature_Selection_in_Generative_Adversarial_Networks_System_aiming_to_detect_DDoS_Attacks.pdf 完整關鍵章節

## Abstract (Page 27)

> With the rapid expansion of global networks and the proliferation of IoT devices, the complexity and scale of traffic have grown exponentially. This surge in connectivity demands larger, faster, and more serviceable architectures, like Software Defined Networks (SDNs). Motivated by various interests, malicious agents seek to compromise services within the network with different attacks. Intrusion Detection Systems (IDSs) are solutions often implemented in SDN using Deep Learning algorithms. These methods are more challenging to explain as they grow in complexity and become less trustworthy for handling sensitive issues like cyber security. This work uses SHapley Additive exPlanations (SHAP) to explain a consolidated IDS that combines Gated Recurrent Units (GRU) with Generative Adversarial Network’s discriminator. We conducted a feature selection based on the SHAP explanation and used its insights to better tune the time series’s window size hyperparameter. The optimized model performed similarly to the original, with a margin for improvement upon further hyperparameter tuning. It was also more stable in the training phase and faster to execute. This new version of the model was also explained by SHAP and presented a more consistent behavior.

* *Index Terms:**XAI, GAN, SDN, DDoS, SHAP, IDS.

- --

## I. Introduction (Page 27)

> Integrating heterogeneous devices, such as smartphones, laptops, and autonomous vehicles, has introduced efficiency and convenience to society. According to Cisco, 500 billion devices will be connected globally by 2030 [1]. Faster networks with more extensive storage capability and serviceability are needed to meet this expectation [2]. Traditional network architectures become more complex and challenging to manage as they grow in size and variety of equipment. Software Defined Networks (SDNs) are a more scalable and straightforward approach to managing. Centralizing control is a trade-off in security as this architecture intrinsically creates a single point of failure, which malicious agents may target to compromise the network services [3].

> Attacks based on flooding, like Distributed Denial of Service (DDoS), have a high potential for compromising SDNs [4]. Systems that continuously monitor traffic and search for suspicious activities are called Network Intrusion Detection Systems (NIDS) and are a solution for defending the network against attackers [5]. Since labeling data is expensive and requires previous knowledge about the invasions, unsupervised solutions based on anomaly detection become promising. These are often implemented based on Deep Learning (DL) algorithms that learn the network’s normal behavior and render an alert of any abnormal occurrence [6].

> A DL algorithm that has been extensively studied in the context of intrusion detection is Generative Adversarial Network (GAN) and its variations [7][8][9]. Due to its complexity, GANs are considered black boxes. These comprise uninterpretable models whose weights and biases cannot be directly understood by humans [10].

> Trustworthiness is a product of understandability when dealing with sensitive and essential solutions such as cyber security [11]. Protection systems are essential to maintain network confidentiality, integrity, and availability. Thus, entrusting crucial decisions to IDS lacking explainability or failing to offer insights into the reasoning behind their outputs can be risky [12]. Explainable AI (XAI) techniques employ various strategies to explain how black box models work internally; this can be leveraged to increase reliability and trust, besides enabling continuous model optimization, which may improve detection efficacy. This transparency increases trust in automated security systems and equips cybersecurity professionals with actionable insights for optimizing the implementation and enabling more informed and effective responses to potential threats. SHapley Additive exPlanations (SHAP) is a widely used method based on cooperative game theory [13][14]. It is employed externally to any already trained model, offering local and global explanations based on feature relevance. SHAP enhances the understandability of the NIDS, clarifying how the traffic features impact the model’s decision-making process.

> This paper aims to apply Kernel SHAP, an implementation for approximating SHAP, in a consolidated Generative Adversarial NIDS for model explanation, feature selection, and hyperparameter tuning. The evaluated black box system is optimized to become more reliable and stable at training, lighter to execute, and less prone to controller overhead.**Contributions:**- Explain a black box Generative Adversarial Network Intrusion Detection System using Kernel SHAP.
- Leverage the model’s explanation to perform feature selection and hyperparameter tuning, yielding a more stable and lighter model.
- Promote trust in the new optimized version of the NIDS by explaining its decision-making process.

> The remainder of this paper is organized as follows. Section II presents the related works. Section III discusses the proposed IDS. In Section IV, we present the interpretation of the proposed model from the perspective of SHAP, selecting the features with more significant roles and time steps, retraining the IDS, and explaining the outcome. Finally, Section V concludes the paper.

- --

## II. Related Works (Pages 27-29)

> SHAP is mainly used to explain the feature’s importance globally in various model classes but can also be leveraged to explain observations alone.

- **Kumar and Ansari [15]**proposed an IDS combining Sheep Flock Optimization Algorithm with Least Absolute Shrinkage and Selection Operator for feature selection. Four ML algorithms were trained and tested on SD-IoT and CIC-IoT-2023 datasets. SHAP interpreted Decision Tree and XGBoost globally, yielding similar feature importances.

- **Sharma et al. [16]**used filter-based feature reduction on NSL-KDD and UNSW-NB15 datasets, applying DNN and CNN IDS variations. DNN performed better and was interpreted using SHAP and LIME, showing key features locally and globally.

- **Hooshmand et al. [17]**proposed a Network Anomaly Detection System using SMOTE and K-means clustering for data imbalance, with a Denoising Autoencoder selecting top 15 features. The NADS used XGBoost explained globally by SHAP, highlighting a roughly linear positive trend between two features.

- **Barnard, Marchetti, and DaSilva [18]**combined supervised XGBoost with unsupervised Deep Autoencoder for zero-day attacks on NSL-KDD. SHAP explained single instances, feeding the Autoencoder to learn typical XGBoost behavior.

- **Arreche, Bibers, and Abdallah [19]**developed a two-level ensemble learning framework with feature selection at both levels using SHAP and Information Gain.

- **Javeed et al. [20]**implemented an IDS combining Bidirectional LSTM, Bidirectional-GRU, fully connected layers, and Softmax classifier on CIC-DDoS2019 dataset. SHAP explained feature importance locally and globally.

- **Kumar et al. [21]**presented a cybersecurity framework integrating blockchain-enabled smart contracts with Digital Twins for Zero-Touch Networks, using SHAP to explain Self-Attention-Based LSTM IDS globally.

- **Hariharan et al. [22]**proposed an IDS framework using four explainability algorithms (Permutation Importance, SHAP, LIME, CIU) on Random Forest, XGBoost, and LightGBM models, demonstrating benefits of combining high prediction performance with interpretability.

- **Oseni et al. [23]**proposed an explainable deep learning framework for IoT-enabled transportation networks using Deep SHAP (combining Deep LIFT with Shapley values) on CNN-based IDS validated on ToN IoT dataset.

> Most works rely on SHAP combined with other XAI techniques like Deep LIFT to elucidate model decisions. Feature selection based on feature importance is often underutilized. Moreover, simultaneous model explanation, feature selection, and hyperparameter tuning, as proposed in this work, are rare in recent intrusion detection studies addressing XAI. This paper aims to fill this gap by applying SHAP to a consolidated GAN-GRU NIDS and performing explanations and optimizations.

- --

## III. Evaluated System (Pages 29-31)

> This section describes the evaluated GAN-GRU system from Lent et al. [24], used as a case study to demonstrate how SHAP can be leveraged for model optimization. The method uses a pre-processed CIC-DDoS2019 dataset containing only volumetric attacks, with entries labeled as attacks but presenting legitimate behavior removed. The attacks remaining are DDoS variations: NetBIOS, LDAP, MSSQL, UDP, and Syn, based on different protocols. This processing is justified by the entropy features used.

### A. Generative Adversarial Network

> A GAN consists of a generator network trained to maximize the error of a discriminator network, which is trained to minimize the same error. Training alternates until no further improvement is possible. At this stage, both networks are independent and can be used to generate realistic samples or act as anomaly detectors.

> The generator requires random noise input to produce different data each iteration, mapping noise to the original data distribution. It never receives real samples directly to avoid unfair advantage.

> The discriminator receives 10 seconds of network traffic to return the probability that the last second contains an anomaly. The generator must create 10 realistic seconds per sample. Since 6 features per second are used, 60 elements must be generated, increasing training and detection complexity.

### B. Gated Recurrent Unit

> GRUs are an evolution of Recurrent Neural Networks (RNNs), which receive previous outputs as context. GRUs improve on RNNs by using gates to control how information is stored or replaced over multiple iterations, enabling longer memory.

> Gates have weights tuned during training. GRUs are efficient for sequential data like time series. For example, a high packet count might be normal alone but anomalous compared to previous seconds.

> The evaluated study experimented with input windows of 5, 10, 15, and 20 seconds, with 10 seconds performing best.

### C. Shannon’s Entropy

> The model uses 6 features: bits per second, packets per second, entropies of source and destination IP, and source and destination port.

> Bits and packets measure traffic volume. Entropies summarize how well traffic is distributed among hosts, allowing neural networks to interpret IP and port occurrences.

> Shannon’s entropy $H$ is calculated as:

$$
H = -\sum_{i=1}^N p_i \log_2(p_i)
$$

where $p_i$ is the probability of occurrence of event $i$ (each IP or port), and $N$ is the number of different events. Probability is computed as the frequency of occurrence divided by total flows.

- --

## IV. SHAP Experimental Analysis (Pages 30-33)

> SHAP, proposed by Lundberg and Lee in 2017 [26], is based on Shapley values from cooperative game theory, distributing payoff among players according to contribution. Here, payoff is model output, players are features.

> SHAP is model-agnostic, post-hoc, additive, and feature importance-based. It can be applied to any trained model after training to explain decisions [27].

> The explanation model is additive:

$$
g(z') = \phi_0 + \sum_{i=1}^M \phi_i z'_i,
$$

where $\phi_0$ is the expected model output (baseline), $\phi_i$ is the contribution of feature $i$, $z' \in \{0,1\}^M$ indicates presence of features, and $M$ is the number of simplified features.

> The classical Shapley value for feature $i$s:

$$
\phi_i = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|! (|F| - |S| - 1)!}{|F|!} \left[ f_{S \cup \{i\}}(x_{S \cup \{i\}}) - f_S(x_S) \right],
$$

where $F$ is the feature set, $S$ is a subset excluding $i$, and $f_S$ is the model prediction using features in $S$.

> Computing exact Shapley values is computationally expensive for many features. Kernel SHAP approximates Shapley values efficiently by combining LIME’s weighted linear regression with Shapley properties.

> LIME minimizes:

$$
\xi = \arg \min_{g \in G} L(f, g, \pi_{x'}) + \Omega(g),
$$

where $L$ measures how well $g$ approximates $f$, $\pi_{x'}$ is a kernel weighting perturbed instances by proximity to $x'$, and $\Omega(g)$ penalizes complexity.

> The Kernel SHAP weighting kernel is:

$$
\pi_{x'}(z') = \frac{(M-1)!}{\binom{M}{|z'|} |z'|! (M - |z'|)!},
$$

where $|z'|$ is the number of non-zero features in $z'$.

> Kernel SHAP provides local explanations that can be aggregated for global feature importance.

### A. Kernel SHAP Analysis

> The system was analyzed using Kernel SHAP on a sample of 120 random seconds per data category from an 8-hour traffic dataset to reduce computation time. Attack entries with benign behavior were removed.

> Fig. 2 (Summary plot) shows average feature impact on model output. Features include entropies of destination port (H(dst port)), destination IP (H(dst ip)), source port (H(src port)), and source IP (H(src ip)), each with time steps (e.g., "packets t-8" is packets per second at step 8 of 10-second window).

> The**most impactful feature was destination port entropy across all time steps except the last**. Other features had less than half the impact.

> Fig. 3 shows interaction between destination port entropy time steps and H(dst ip) t-0 (10th most important). Destination port entropy shows positive SHAP values from time steps 0 to 7, indicating influence toward predicting attacks, consistent with data distribution.

> Fig. 4 shows interactions between other features without destination port entropy, revealing scattered SHAP values without clear trends.

> Fig. 5 analyzes six traffic types (a-f):

- (a) Destination port entropy is most influential at time steps 2, 6, 4; features cluster near zero for normal traffic.
- (b) H(dst port) time steps 0-7 strongly influence positive attack prediction; H(dst ip) t-0 hinders attack prediction.
- (c) Similar to (b), H(dst port) time steps 0-7 push positive predictions; others are balanced or negative.
- (d) Similar behavior to (c).
- (e) Less variation but destination port entropy tends positive at steps 3-7.
- (f) Wider spread; H(dst port) time steps 0-7 critical; H(src ip) t-3 hinders prediction.

> Motivated by the dominant role of H(dst port) time steps 0-7 and less impactful or detrimental influence of other features, **all features except destination port entropy were removed**, and the window size reduced from 10 to 8 seconds.

> The GAN-GRU model was retrained with only this feature, yielding similar results without hyperparameter changes. The model trained more consistently and executed faster.

> Fig. 6 shows the optimized model’s SHAP summary plots with more defined feature impact and less spread around zero.

> Performance metrics:

- Original model: MCC = 0.97, 34 false positives, 44 false negatives.
- Optimized model: MCC = 0.95, 6 false negatives, 158 false positives.

> Further hyperparameter tuning is suggested for fair comparison.

- --

## V. Conclusion (Page 33)

> This paper evaluated a consolidated black box GAN-GRU Network Intrusion Detection System using Kernel SHAP. The model used a 10-second sliding window to infer the last second. The dataset’s evaluation day comprises 8 hours of network traffic; samples were analyzed globally and per data type.

> SHAP explanations identified **destination port entropy as the most impactful feature**for anomaly detection, with other features showing inconclusive behavior.

> Retraining the NIDS with only this feature reduced MCC from 0.97 to 0.95 but improved training stability and reduced computational cost, producing a lighter model minimizing controller overhead.

> Hyperparameters and thresholds were kept from the original model, indicating potential for improvement through re-tuning to address increased false positives.

> The destination port entropy showed more concentrated SHAP values, indicating clearer model behavior.

> This study demonstrates how SHAP can be used for model explanation, feature selection, and hyperparameter tuning, yielding a lighter, more interpretable, and trustworthy model.**Future Work:**- Explore other XAI techniques such as LIME and Deep SHAP applied to GAN-GRU NIDS and other state-of-the-art methods.
- Assess whether alternative explainability methods offer additional benefits in model optimization, detection performance, and reliability.

- --

## Acknowledgment (Page 33)

> This work has been partially supported by the National Council for Scientific and Technological Development (CNPq) of Brazil under the grant of Project 306397/2022-6 and concession of scholarships.

- --

## References (Pages 33-34)

> [1] Y. B. Zikria et al., “Next-generation internet of things (iot): Opportunities, challenges, and solutions,” Sensors, vol. 21, no. 4, 2021.  
> [2] A. A. Toony et al., “Multi-block: A novel ml-based intrusion detection framework for sdn-enabled iot networks using new pyramidal structure,” Internet of Things, vol. 26, p. 101231, 2024.  
> ...  
> [24] D. M. Brandão Lent et al., “An unsupervised generative adversarial network system to detect ddos attacks in sdn,” IEEE Access, vol. 12, pp. 70 690–70 706, 2024.  
> [25] C. E. Shannon, “A mathematical theory of communication,” The Bell System Technical Journal, vol. 27, no. 3, pp. 379–423, 1948.  
> [26] S. M. Lundberg and S.-I. Lee, “A unified approach to interpreting model predictions,” Advances in neural information processing systems, vol. 30, 2017.  
> [27] A. Theissler et al., “Explainable ai for time series classification: A review, taxonomy and research directions,” IEEE Access, vol. 10, pp. 100 700–100 724, 2022.  
> [28] M. T. Ribeiro et al., “Why should i trust you?: Explaining the predictions of any classifier,” in Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 2016, pp. 1135–1144.

- --

# Technical Explanation Notes

- **Generative Adversarial Networks (GANs):**Comprise two neural networks, a generator and a discriminator, trained adversarially. The generator tries to produce realistic data to fool the discriminator, which tries to distinguish real from fake data.

- **Gated Recurrent Units (GRUs):**A type of recurrent neural network cell designed to capture dependencies in sequential data by controlling information flow with gates, enabling longer memory than vanilla RNNs.

- **Shannon’s Entropy:**Measures uncertainty or randomness in data distribution. Lower entropy indicates dominance of few elements; higher entropy indicates more uniform distribution.

- **SHapley Additive exPlanations (SHAP):**A method to explain model predictions by attributing contributions to each feature based on cooperative game theory, ensuring fair distribution of "credit" for the prediction.

- **Kernel SHAP:**An efficient approximation of Shapley values using a weighted linear regression surrogate model, enabling explanation of complex black-box models.

- **Matthews Correlation Coefficient (MCC):**A balanced metric for binary classification performance, considering true/false positives and negatives, ranging from -1 (worst) to +1 (best).

- --

# Important Findings and Claims

- Destination port entropy is the**dominant feature**influencing the GAN-GRU IDS’s decision-making for DDoS detection.

- Feature selection based on SHAP allowed reducing input features and window size, producing a**lighter, faster, and more stable model**with only a slight decrease in MCC.

- SHAP explanations provide**transparent insights**into black-box IDS models, promoting trust and enabling model optimization.

- The approach demonstrates the**feasibility of combining explainability, feature selection, and hyperparameter tuning** in intrusion detection systems.

- Future work should explore other XAI methods and further hyperparameter tuning to improve detection performance and reduce false positives.

- --

以上即為該論文的完整關鍵章節內容提取與說明。

---

> **注意**：本文檔包含數學公式，請使用支持LaTeX數學渲染的Markdown查看器（如VS Code + Markdown Math插件、Typora、JupyterLab等）以獲得最佳顯示效果。