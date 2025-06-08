# Explainable_AI_Feature_Selection_in_Generative_Adversarial_Networks_System_aiming_to_detect_DDoS_Attacks.pdf 深度分析

# 深度分析報告：Explainable AI Feature Selection in Generative Adversarial Networks System aiming to detect DDoS Attacks

- --

## 1. 論文標題與作者

* *論文標題**Explainable AI Feature Selection in Generative Adversarial Networks System aiming to detect DDoS Attacks**作者**  
- Mateus Komarchesqui (Computer Science Department, State University of Londrina, Brazil)  
- Daniel Matheus Brandão Lent (Electrical Engineering Department, State University of Londrina, Brazil)  
- Vitor Gabriel da Silva Ruffo (Electrical Engineering Department, State University of Londrina, Brazil)  
- Luiz Fernando Carvalho (Federal Technology University of Paraná, Brazil)  
- Jaime Lloret (Integrated Management Coastal Research Institute, Universitat Politecnica de Valencia, Spain)  
- Mario Lemes Proença Jr. (Computer Science Department, State University of Londrina, Brazil)

- --

## 2. 研究背景與問題陳述

隨著全球網路和物聯網（IoT）設備的快速擴張，網路流量的複雜度和規模呈指數成長。為了因應龐大且多樣化的設備，軟體定義網路（SDN）成為一種可擴展且易管理的架構。然而，SDN的集中控制特性也帶來單點故障的安全風險，容易成為惡意攻擊目標，尤其是分散式阻斷服務攻擊（DDoS）。

傳統的入侵偵測系統（IDS）結合深度學習（DL）技術，能有效偵測異常流量，但深度學習模型通常為黑盒模型，缺乏解釋性，降低了系統的可信度與可用性。**本研究旨在利用解釋性人工智慧（XAI）技術，特別是SHapley Additive exPlanations（SHAP），來解釋並優化一個結合生成對抗網路（GAN）與門控循環單元（GRU）的入侵偵測系統，提升模型的透明度、穩定性與執行效率。**---

## 3. 研究方法詳述

### 3.1 系統架構

- **生成對抗網路（GAN）**：包含生成器與判別器兩個網路，生成器嘗試生成逼真的流量樣本以欺騙判別器，判別器則學習辨識真實與偽造樣本。此系統使用判別器作為異常偵測器。
- **門控循環單元（GRU）**：用於處理時間序列資料，能記憶長期依賴資訊，適合分析連續的網路流量特徵。
- **特徵選擇**：使用6個特徵，包括每秒位元數、封包數，以及來源與目的IP與端口的Shannon熵。

### 3.2 解釋方法

- **SHAP（SHapley Additive exPlanations）**：基於合作博弈論的Shapley值，量化每個特徵對模型輸出的貢獻。  
- **Kernel SHAP**：結合LIME與Shapley值的近似方法，降低計算複雜度，適用於黑盒模型的後設解釋。

### 3.3 實驗設計

- 使用CIC-DDoS2019資料集，聚焦於體積型DDoS攻擊（NetBIOS、LDAP、MSSQL、UDP、Syn）。
- 隨機抽取120秒的樣本以降低SHAP計算成本。
- 分析SHAP值以識別最重要的特徵與時間步長。
- 基於SHAP結果進行特徵選擇與時間窗口調整（由10秒縮減至8秒）。
- 重新訓練模型並比較性能與穩定性。

- --

## 4. 主要發現與結果

- **SHAP分析結果**顯示，**目的端口熵（H(dst port)）在時間步0至7對模型輸出影響最大**，其他特徵影響較小且不穩定。
- 移除其他特徵，僅保留目的端口熵，並將時間窗口縮短至8秒後，模型性能略有下降（MCC從0.97降至0.95），但訓練更穩定且執行速度更快。
- 優化後模型的假陽性數量增加，假陰性數量減少，顯示需要進一步調整超參數以平衡性能。
- SHAP解釋優化後模型的決策過程更為一致且易於理解。

- --

## 5. 核心創新點

- **結合SHAP解釋與GAN-GRU黑盒入侵偵測系統進行特徵選擇與超參數調整**，同時提升模型的可解釋性與運算效率。
- 利用XAI技術不僅解釋模型決策，還用於**模型優化**，這在現有文獻中較少見。
- 提出一套流程，從模型解釋到特徵篩選再到超參數調整，形成閉環優化。

- --

## 6. 結論與影響

- SHAP成功揭示了GAN-GRU模型中最關鍵的特徵，促使模型簡化且更穩定。
- 優化後的模型在保持高偵測性能的同時，降低了計算負擔，減少SDN控制器的負載。
- 研究強調XAI在網路安全領域的應用價值，提升了IDS系統的透明度與可信度，有助於安全專家理解與調整模型。
- 為未來基於深度學習的IDS提供了可解釋性與優化的範例。

- --

## 7. 局限性與未來研究方向

- **局限性**：
  - 優化後模型的假陽性率增加，尚需透過超參數調整進一步改善。
  - 研究僅使用Kernel SHAP，未比較其他XAI方法的效果。
  - 僅針對特定DDoS攻擊類型與資料集進行驗證，泛化能力待評估。

- **未來方向**：
  - 探索其他XAI技術（如LIME、Deep SHAP）對GAN-GRU IDS的解釋與優化效果。
  - 進行超參數與閾值的系統性調整，提升優化模型的偵測準確度與穩定性。
  - 擴展至更多攻擊類型與多樣化資料集，驗證方法的普適性。
  - 探討XAI技術在實時IDS部署中的實用性與效率。

- --

## 8. 關鍵術語與概念解釋

- **生成對抗網路（GAN）**：由生成器與判別器組成的神經網路架構，生成器試圖創造逼真數據以欺騙判別器，判別器則學習辨識真實與偽造數據。
- **門控循環單元（GRU）**：一種改良的循環神經網路，透過門控機制控制資訊流動，適合處理時間序列資料。
- **Shannon熵**：衡量資訊隨機性或不確定性的指標，應用於網路流量中用以描述IP或端口分布的均勻程度。
- **SHapley Additive exPlanations（SHAP）**：基於合作博弈論的解釋方法，計算每個特徵對模型預測的貢獻值。
- **Kernel SHAP**：SHAP的一種近似計算方法，結合LIME的局部線性模型與Shapley值，降低計算複雜度。
- **MCC（Matthews Correlation Coefficient）**：衡量二分類模型性能的指標，綜合考慮真陽性、真陰性、假陽性與假陰性。

- --

## 9. 總體評價

- **重要性**：本研究針對SDN環境下DDoS攻擊偵測，結合先進的深度學習與XAI技術，解決了黑盒模型缺乏解釋性的問題，對網路安全領域具有實際應用價值。
- **可靠性**：實驗基於公開且具代表性的CIC-DDoS2019資料集，採用嚴謹的隨機抽樣與多角度分析，結果具有說服力。
- **創新性**：首次將SHAP用於GAN-GRU IDS的特徵選擇與超參數調整，形成解釋與優化的閉環，填補了現有文獻的空白。
- **改進空間**：未來可進一步優化模型性能，並擴展XAI方法的比較研究。

- --

## 10. 參考文獻（部分關鍵）

1. D. M. Brandão Lent, V. G. da Silva Ruffo, L. F. Carvalho, J. Lloret, J. J. P. C. Rodrigues, and M. Lemes Proença, “An unsupervised generative adversarial network system to detect ddos attacks in sdn,” _IEEE Access_, vol. 12, pp. 70690–70706, 2024. [DOI: 10.1109/ACCESS.2024.XXXXXXX]

2. S. M. Lundberg and S.-I. Lee, “A unified approach to interpreting model predictions,” _Advances in Neural Information Processing Systems_, vol. 30, 2017.

3. C. E. Shannon, “A mathematical theory of communication,” _The Bell System Technical Journal_, vol. 27, no. 3, pp. 379–423, 1948.

4. B. Sharma, L. Sharma, C. Lal, and S. Roy, “Explainable artificial intelligence for intrusion detection in iot networks: A deep learning based approach,” _Expert Systems with Applications_, vol. 238, p. 121751, 2024.

5. A. Oseni, N. Moustafa, G. Creech, N. Sohrabi, A. Strelzoff, Z. Tari, and I. Linkov, “An explainable deep learning framework for resilient intrusion detection in iot-enabled transportation networks,” _IEEE Transactions on Intelligent Transportation Systems_, vol. 24, no. 1, pp. 1000–1014, 2023.

6. M. T. Ribeiro, S. Singh, and C. Guestrin, “Why should I trust you?: Explaining the predictions of any classifier,” in _Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining_, 2016, pp. 1135–1144.

- --

# 總結

本論文成功展示了如何利用SHAP解釋技術對GAN-GRU入侵偵測系統進行特徵重要性分析，並基於此進行特徵選擇與時間窗口調整，達成模型輕量化與穩定化。此研究不僅提升了IDS的解釋性與可信度，也為未來結合XAI與深度學習的網路安全系統優化提供了寶貴參考。

---

> **注意**：本文檔包含數學公式，請使用支持LaTeX數學渲染的Markdown查看器（如VS Code + Markdown Math插件、Typora、JupyterLab等）以獲得最佳顯示效果。