# Task A: Base LLM vs RAG (25 questions)

Generator: Qwen2.5-7B-Instruct · Retriever: bge-m3 + bge-reranker-v2-m3 (top-5) · Judge: Phi-4 (4-bit)

| Metric | Base (no RAG) | RAG |
|---|---|---|
| Accuracy (correct=1, partial=0.5) | 28.0% | 96.0% |
| Accuracy, raw judge (before manual review) | 28.0% | 96.0% |
| Strict accuracy (correct only) | 8.0% | 92.0% |
| Grounding (yes=1, partial=0.5) | 0% (no sources) | 94.0% |
| Answers with citations | 0% | 100.0% |
| Retrieval hit@5 (expected doc retrieved) | n/a | 88.0% |

## Verdict counts

| Verdict | Base | RAG |
|---|---|---|
| correct | 2 | 23 |
| partial | 10 | 2 |
| incorrect | 13 | 0 |
| unparsed | 0 | 0 |

## By topic (accuracy)

| Topic | N | Base | RAG |
|---|---|---|---|
| A1 | 5 | 30% | 100% |
| E2 | 8 | 25% | 100% |
| E2AP | 1 | 0% | 100% |
| Near-RT RIC | 3 | 67% | 83% |
| Architecture | 3 | 17% | 100% |
| AI/ML | 2 | 50% | 100% |
| Papers | 3 | 0% | 83% |

## Base hallucinated, RAG correct (12 cases)

### Q1. What does the A1 interface do?
- **Reference:** A1 connects the Non-RT RIC (in the SMO) with the Near-RT RIC. It carries policy management (declarative A1 policies that guide the Near-RT RIC/RAN), A1 enrichment information from Non-RT RIC to Near-RT RIC, ML model management / training-related messages, and policy status and feedback from the Near-RT RIC back to the Non-RT RIC.
- **Base (incorrect):** The A1 interface in O-RAN is used for communication between the Radio Unit (RU) and the Distributed Unit (DU). It facilitates the exchange of radio signals, control information, and synchronization data.
  - _Judge:_ The candidate answer describes the A1 interface as connecting the Radio Unit (RU) and the Distributed Unit (DU), which is incorrect; the reference specifies that A1 connects the Non-RT RIC with the Near-RT RIC.
- **RAG (correct):** The A1 interface serves several key functions as outlined in the context:

- It enables communication between Non-RT RIC in the SMO and Near-RT RIC in the RAN [1][2].
- It supports the transfer of policy management information, policy status and feedback, and the discovery and request of enrichment information [2].
- It facilitates the exchange of AI/ML model training related messages between SMO/Non-RT RIC and Near-RT RIC [2][3].
- It allows for the creation, modification, and deletion of A1 policies [5].
- It provides mechanisms for Near-RT RIC to discover and request delivery of enrichment information [1][2].
- It enables the transmission of A1 enrichment information from Non-RT RIC to Near-RT RIC as needed [1][2].
- It supports the authorization of requests to access A1 services [3].

These functions collectively enable a flexible, multi-vendor environment where Non-RT RIC can guide Near-RT RIC towards fulfilling RAN intent through policy-based guidance and enriched information [1][5].
- **Cited passage [1]** `O-RAN.WG2.TS.A1GAP-R005-v05.04.pdf` p.9-10:
  > A1 interface, two types of enrichment information are distinguished: A1 enrichment information and external enrichment information. The A1 interface is used for discovery, request, and delivery of A1 enrichment information. The A1 interface is also used for the discovery of external enrichment information and the SMO / Non-RT RIC is responsible for the authentication of the source and the security of the direct connection. NOTE: The handling of direct connections, and discovery or delivery of external enrichment information involving the A1 interface is not defined in the present [...]

### Q2. Between which two O-RAN entities is the A1 interface defined?
- **Reference:** Between the Non-RT RIC (part of the SMO) and the Near-RT RIC.
- **Base (incorrect):** The A1 interface is defined between the Radio Unit (RU) and the Remote Radio Unit (RRU) in O-RAN.
  - _Judge:_ The candidate answer incorrectly identifies the A1 interface as being between the RU and RRU, whereas the reference specifies it is between the Non-RT RIC and the Near-RT RIC.
- **RAG (correct):** The A1 interface is defined between the Non-RT RIC in the SMO and the Near-RT RIC function [1][3][4].
- **Cited passage [1]** `O-RAN.WG2.TS.A1GAP-R005-v05.04.pdf` p.9-10:
  > A1 interface, two types of enrichment information are distinguished: A1 enrichment information and external enrichment information. The A1 interface is used for discovery, request, and delivery of A1 enrichment information. The A1 interface is also used for the discovery of external enrichment information and the SMO / Non-RT RIC is responsible for the authentication of the source and the security of the direct connection. NOTE: The handling of direct connections, and discovery or delivery of external enrichment information involving the A1 interface is not defined in the present [...]

### Q3. What are A1 policies and what is their purpose?
- **Reference:** A1 policies are declarative policies containing statements on policy objectives and policy resources applicable to e.g. UEs and cells. Their purpose is to let the Non-RT RIC guide the Near-RT RIC, and hence the RAN, towards better fulfilment of the RAN intent.
- **Base (incorrect):** A1 policies in O-RAN refer to admission control policies that determine whether a new connection or service can be established based on network resource availability. Their purpose is to ensure efficient use of network resources by controlling the number of active connections and preventing overloading of the network.
  - _Judge:_ The candidate answer describes A1 policies as admission control policies, which contradicts the reference answer that defines them as declarative policies guiding the RIC towards fulfilling RAN intent.
- **RAG (correct):** A1 policies are declarative policies that contain statements on policy objectives and policy resources applicable to entities like UEs and cells [1][3]. Their purpose is to enable the Non-RT RIC function in the SMO to guide the Near-RT RIC function, and thus the RAN, towards better fulfillment of the RAN intent [2].
- **Cited passage [1]** `O-RAN.WG2.TS.A1GAP-R005-v05.04.pdf` p.8-9:
  > The purpose of the A1 policies is to guide the RAN performance towards the overall goal expressed in RAN intent. The A1 policies are declarative policies that contain statements on policy objectives and policy resources applicable to e.g. UEs and cells. The Non-RT RIC can manage the A1 policies based on A1 policy status and feedback information provided by the Near-RT RIC, and on the network status provided over O1. The Non-RT RIC can use the O1 observables to continuously evaluate the impact of the A1 policies towards fulfilment of the RAN intent and based on internal conditions it can [...]

### Q6. Which RIC services can the Near-RT RIC use from an E2 Node?
- **Reference:** REPORT, INSERT, CONTROL, POLICY and QUERY.
- **Base (incorrect):** The Near-RT RIC can use RAN Configuration and Measurement Services from an E2 Node.
  - _Judge:_ The candidate answer lists RAN Configuration and Measurement Services, which are not mentioned in the reference answer.
- **RAG (correct):** The Near-RT RIC can use several RIC services from an E2 Node, including REPORT, INSERT, CONTROL, POLICY, QUERY, and ASSISTANCE [1][3].
- **Cited passage [1]** `O-RAN.WG3.TS.E2GAP-R005-v09.00.pdf` p.10-11:
  > Near-RT RIC; - Enables the Near-RT RIC to control selected RAN functions on the E2 Node. © 2026 by the O-RAN ALLIANCE e.V. Your use is subject to the copyright statement on the cover page of this specification. 11 O-RAN.WG3.TS.E2GAP-R005-v09.00 5.3 Functions of the E2 interface 5.3.1 General The E2 functions are grouped into the following categories: RIC services supported by RIC functional procedures: - RIC Services (REPORT, INSERT, CONTROL, POLICY, QUERY and ASSISTANCE), as described in clause 5.3.2) supported by RIC functional procedures (RIC Subscription, RIC Subscription [...]

### Q9. How many Near-RT RICs can a single E2 Node be connected to?
- **Reference:** Only one. An E2 Node is connected to only one Near-RT RIC, while a Near-RT RIC can be connected to multiple E2 Nodes.
- **Base (incorrect):** The number of Near Real-Time (Near-RT) Radio Intelligence Components (RICs) that a single E2 Node can be connected to is not strictly defined by the O-RAN Alliance specifications. However, in practice, it depends on the E2 Node's capacity and the network design. Typically, an E2 Node can support multiple Near-RT RICs, often in the range of 10 to 50 or more, depending on the specific implementation and requirements.
  - _Judge:_ The candidate answer contradicts the reference by stating that an E2 Node can support multiple Near-RT RICs, whereas the reference specifies that an E2 Node is connected to only one Near-RT RIC.
- **RAG (correct):** According to the context provided, a Near-RT RIC can be connected to multiple E2 Nodes, but a single E2 Node is connected to only one Near-RT RIC [1].
- **Cited passage [1]** `O-RAN.WG3.TS.E2GAP-R005-v09.00.pdf` p.8-9:
  > E2 Node E2 Near-RT RIC E2 E2 E2 Node O-eNB E2 E1 Open Fronthaul F1-u Figure 4.2-1: O-RAN architecture overview showing Near-RT RIC interfaces With respect to the E2 interface: © 2026 by the O-RAN ALLIANCE e.V. Your use is subject to the copyright statement on the cover page of this specification. 9 O-RAN.WG3.TS.E2GAP-R005-v09.00 - E2 is a logical interface connecting the Near-RT RIC with an E2 Node: - The Near-RT RIC is connected to the O-CU-CP; - The Near-RT RIC is connected to the O-CU-UP; - The Near-RT RIC is connected to the O-DU; - The Near-RT RIC is connected to the O-eNB. - An E2 [...]

### Q10. What latency range must the E2 interface support for near-real-time optimization?
- **Reference:** From 10 milliseconds up to 1 second.
- **Base (incorrect):** The E2 interface in O-RAN must support a latency range of less than 10 milliseconds to enable near-real-time optimization.
  - _Judge:_ The candidate answer states a latency range of less than 10 milliseconds, which contradicts the reference answer's range of 10 milliseconds up to 1 second.
- **RAG (correct):** The E2 interface must support latency requirements for near-real-time optimization, ranging from 10 milliseconds up to 1 second [1].
- **Cited passage [1]** `O-RAN.WG3.TS.E2GAP-R005-v09.00.pdf` p.8-9:
  > E2 Node E2 Near-RT RIC E2 E2 E2 Node O-eNB E2 E1 Open Fronthaul F1-u Figure 4.2-1: O-RAN architecture overview showing Near-RT RIC interfaces With respect to the E2 interface: © 2026 by the O-RAN ALLIANCE e.V. Your use is subject to the copyright statement on the cover page of this specification. 9 O-RAN.WG3.TS.E2GAP-R005-v09.00 - E2 is a logical interface connecting the Near-RT RIC with an E2 Node: - The Near-RT RIC is connected to the O-CU-CP; - The Near-RT RIC is connected to the O-CU-UP; - The Near-RT RIC is connected to the O-DU; - The Near-RT RIC is connected to the O-eNB. - An E2 [...]

### Q11. Which transport protocol carries E2AP signalling between the E2 Node and the Near-RT RIC?
- **Reference:** SCTP over IP (one or more SCTP associations between the E2 Node and Near-RT RIC pair); E2AP is the application-layer signalling protocol.
- **Base (incorrect):** The E2AP signalling between the E2 Node and the Near-RT RIC is carried over the E2 transport protocol, which uses UDP (User Datagram Protocol) for transport.
  - _Judge:_ The candidate answer incorrectly states that E2AP signalling uses UDP, while the reference specifies SCTP over IP.
- **RAG (correct):** The transport protocol that carries E2AP signalling between the E2 Node and the Near-RT RIC is SCTP [1][2].
- **Cited passage [1]** `O-RAN.WG3.TS.E2GAP-R005-v09.00.pdf` p.43-45:
  > IC decides to start/stop \nLoad measurement to E2 Node near->ran: E2 RESOURCE STATUS REQUEST note over ran #white: E2 Node Start/stop the requested measurement \naccording to the parameters given in the request near<-ran: E2 RESOURCE STATUS RESPONSE @enduml © 2026 by the O-RAN ALLIANCE e.V. Your use is subject to the copyright statement on the cover page of this specification. 44 O-RAN.WG3.TS.E2GAP-R005-v09.00 Figure 5.5.7-1: E2 Resource Status procedure 5.5.8 E2 Resource Status Update The E2 Resource Status Update is used by the E2 Node to inform the Near-RT RIC of the results of the [...]

### Q12. Into which two modules are E2AP procedures divided?
- **Reference:** RIC Functional Procedures (application-specific messages between Near-RT RIC applications and a target RAN Function) and Global Procedures (not directly related to a specific application).
- **Base (incorrect):** E2AP procedures are divided into two modules: E2 Setup and E2 Control.
  - _Judge:_ The candidate answer incorrectly identifies E2AP procedures as E2 Setup and E2 Control, whereas the reference specifies RIC Functional Procedures and Global Procedures.
- **RAG (correct):** E2AP procedures are divided into two modules as follows:
1. RIC Functional Procedures;
2. Global Procedures. [1][2]
- **Cited passage [1]** `O-RAN.WG3.TS.E2AP-R005-v09.00.docx` §4.3	Specification notations … §8.1	Elementary procedures:
  > case characters and all letters in Italic font followed by the abbreviation "IE", e.g. E-RAB ID IE. Value of an IE When referring to the value of an Information Element (IE) in the present document the "Value" is written as it is specified in the present document enclosed by quotation marks, e.g. "Value". 5 E2AP Services 5.1 E2AP procedure modules The E2 interface E2AP procedures are divided into two modules as follows: 1. RIC Functional Procedures; 2. Global Procedures. The RIC functional procedures module contains procedures used to pass application specific messages between Near-RT [...]

### Q18. Which interfaces does the Near-RT RIC platform support?
- **Reference:** A1, E2, Y1 and O1.
- **Base (incorrect):** The Near Real-Time Radio Resource Control (RRC) Interface (NRF-RIC) platform supports the O-RAN Alliance's Near-RT RIC interface (O-RAN Spec 074), which includes the following key interfaces:

1. **RIC to RAN Interface (RRI)**: This is the primary interface between the RIC and the RAN.
2. **RIC to NFV Infrastructure Interface**: This interface connects the RIC with the underlying NFV infrastructure.

These interfaces enable the RIC to perform real-time control and optimization of radio resources in the RAN.
  - _Judge:_ The candidate answer does not mention the specific interfaces A1, E2, Y1, and O1 as required by the reference answer.
- **RAG (correct):** The Near-RT RIC platform supports A1, E2, Y1, and O1 interfaces [3][4].
- **Cited passage [3]** `O-RAN.WG3.TS.RICARCH-R005-v09.00.docx` §2.2	Informative references … §5.1.1	Platform Requirements:
  > necessary for the application of the present document, but they assist the user with regard to a particular subject area. [i.1] 3GPP TR 21.905: “Vocabulary for 3GPP Specifications”. 3 Definition of terms, symbols and abbreviations 3.1 Terms For the purposes of the present document, the terms given in 3GPP TR 21.905 [i.1], O-RAN.WG1.TS.OAD [10] and the following apply: Void. 3.2 Symbols For the purposes of the present document, the symbols given in [i.1] and the following apply: Void. 3.3 Abbreviations For the purposes of the present document, the abbreviations given in [i.1] and the [...]

### Q19. What is the O2 interface used for?
- **Reference:** O2 is the interface between the SMO and the O-Cloud, providing O-Cloud resource management and workload management.
- **Base (incorrect):** The O2 interface in O-RAN is used for remote radio unit (RRU) management, allowing for the control and monitoring of RRU functions from a centralized unit or cloud environment.
  - _Judge:_ The candidate answer incorrectly describes the O2 interface as being used for RRU management, whereas the reference specifies it is for O-Cloud resource and workload management.
- **RAG (correct):** The O2 interface is used for providing secured communication between the SMO (Service Management and Orchestration) and the O-Cloud. It enables the management of O-Cloud infrastructures and the deployment life cycle management of O-RAN cloudified NFs (Network Functions) that run on the O-Cloud [2][3].
- **Cited passage [2]** `O-RAN.WG6.TS.O2-GA&P-R005-v11.00.pdf` p.8-10:
  > CPUs, Memories, Storages, NICs, HW Accelerators, etc. O-Cloud Node Cluster: a collection of O-Cloud Nodes that work in concert with each other, through a set of interconnecting O-Cloud Node Cluster Site Networks. O-Cloud Platform: a platform comprising hardware and software that provides O-Cloud capabilities and services to execute RAN network functions. 1.3.2 Symbols Void 1.3.3 Abbreviations For the purposes of the present document, the abbreviations [given in [i.1] and the following] apply: NOTE: An abbreviation defined in the present document takes precedence over the definition of [...]

### Q23. What is ORAN-Bench-13K and how many difficulty levels does it have?
- **Reference:** An open-source benchmark of 13,952 multiple-choice questions generated from 116 O-RAN specification documents for evaluating LLMs on O-RAN, categorized into three difficulty levels (easy, intermediate, difficult).
- **Base (incorrect):** ORAN-Bench-13K is a benchmarking framework for Open RAN (O-RAN) systems, designed to evaluate the performance of O-RAN compliant components. It has 5 difficulty levels to assess the complexity and capabilities of different O-RAN solutions.
  - _Judge:_ The candidate answer incorrectly states that ORAN-Bench-13K has 5 difficulty levels, whereas the reference specifies 3 difficulty levels.
- **RAG (correct):** ORAN-Bench-13K is a benchmark designed to evaluate the performance of Large Language Models (LLMs) within the context of O-RAN [1]. It consists of 13,952 meticulously curated multiple-choice questions generated from 116 O-RAN specification documents and is categorized into three distinct difficulty levels: easy, intermediate, and difficult [1].
- **Cited passage [1]** `ORAN-Bench-13K.pdf` p.1:
  > ORAN-Bench-13K: An Open Source Benchmark for Assessing LLMs in Open Radio Access Networks Pranshav Gajjar and Vijay K. Shah NextG Wireless Lab, George Mason University pgajjar@gmu.edu and vshah22@gmu.edu Abstract—Large Language Models (LLMs) can revolutionize how we deploy and operate Open Radio Access Networks (O- RAN) by enhancing network analytics, anomaly detection, and code generation and significantly increasing the efficiency and reliability of a plethora of O-RAN tasks. In this paper, we present ORAN-Bench-13K, the first comprehensive benchmark designed to evaluate the [...]

### Q24. What is RANSTRUCT in ORANSight-2.0?
- **Reference:** A RAG-based instruction-tuning framework using two LLM agents, a Mistral-based Question Generator and a Qwen-based Answer Generator, to create instruction-tuning datasets used to fine-tune 18 open-source LLMs via QLoRA.
- **Base (incorrect):** RANSTRUCT in ORANSight-2.0 refers to the Radio Access Network (RAN) structure visualization feature, which helps in understanding and managing the architecture of an O-RAN compliant RAN. It provides a graphical representation of the RAN components and their interconnections.
  - _Judge:_ The candidate answer describes RANSTRUCT as a visualization feature, which is unrelated to the reference answer's description of a RAG-based instruction-tuning framework.
- **RAG (correct):** RANSTRUCT in ORANSight-2.0 is a Retrieval-Augmented Generation (RAG)-based instruction-tuning framework that leverages two LLM agents to generate high-quality, O-RAN-specific instruction-tuning datasets [2][3]. It uses a Mistral-based Question Generator and a Qwen-based Answer Generator to create these datasets [3].
- **Cited passage [2]** `ORANSight-2.0.pdf` p.1-2:
  > O-RAN-related challenges. Additionally, we pro- posed a preliminary version of ORANSight, which addressed domain-based limitations by leveraging Retrieval-Augmented Generation (RAG) [11]. Similarly, Karbalaee Motalleb et al. [14] explored the use of LLMs to enhance the security of O-RAN architectures, emphasizing the necessity of domain- specific fine-tuning to mitigate vulnerabilities and threats. Furthermore, Lotfi et al. [15] demonstrated the effectiveness of LLM-augmented Deep Reinforcement Learning (DRL) for Fig. 1. Overall pipeline for ORANSight-2.0 models. dynamic O-RAN network [...]

## RAG not fully correct (2 cases), for the error analysis

- **Q16** (partial, retrieval hit=True): What does the Messaging Infrastructure function of the Near-RT RIC provide? | The candidate answer provides additional details but does not explicitly mention low-latency message delivery between Near-RT RIC internal endpoints.
- **Q25** (partial, retrieval hit=True): What is srsRANBench? | The candidate answer lacks the specific context of O-RAN specifications and the introduction with ORANSight-2.0.
