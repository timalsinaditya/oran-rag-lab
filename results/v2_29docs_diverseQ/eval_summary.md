# Task A: Base LLM vs RAG (25 questions)

Generator: Qwen2.5-7B-Instruct · Retriever: bge-m3 + bge-reranker-v2-m3 (top-5) · Judge: Phi-4 (4-bit)

| Metric | Base (no RAG) | RAG |
|---|---|---|
| Accuracy (correct=1, partial=0.5) | 18.0% | 90.0% |
| Accuracy, raw judge (before manual review) | 18.0% | 88.0% |
| Strict accuracy (correct only) | 4.0% | 80.0% |
| Grounding (yes=1, partial=0.5) | 0% (no sources) | 88.0% |
| Answers with citations | 0% | 92.0% |
| Retrieval hit@5 (expected doc retrieved) | n/a | 91.3% |

## Verdict counts

| Verdict | Base | RAG |
|---|---|---|
| correct | 1 | 20 |
| partial | 7 | 5 |
| incorrect | 17 | 0 |
| unparsed | 0 | 0 |

## By topic (accuracy)

| Topic | N | Base | RAG |
|---|---|---|---|
| WG1 SMO | 1 | 0% | 100% |
| WG1 Energy saving | 1 | 50% | 100% |
| WG1 Slicing | 1 | 0% | 50% |
| WG1 Architecture | 1 | 50% | 50% |
| WG2 R1 | 1 | 0% | 100% |
| WG2 R1/A1 | 1 | 0% | 100% |
| WG2 A1 | 1 | 0% | 100% |
| WG3 E2 | 3 | 0% | 100% |
| WG3 E2SM-KPM | 2 | 25% | 75% |
| WG3 E2SM-RC | 1 | 50% | 100% |
| WG3 Y1 | 1 | 0% | 100% |
| WG4 Fronthaul | 2 | 25% | 100% |
| WG5 D2 | 1 | 0% | 100% |
| WG6 Cloud | 1 | 0% | 100% |
| WG8 Stack | 1 | 0% | 100% |
| WG9 Transport | 1 | 0% | 100% |
| WG10 OAM | 1 | 0% | 50% |
| WG11 Security | 2 | 50% | 75% |
| Unanswerable | 2 | 50% | 100% |

## By question type (accuracy)

| Type | N | Base | RAG |
|---|---|---|---|
| list | 6 | 25% | 100% |
| definition | 9 | 6% | 83% |
| comparison | 2 | 50% | 75% |
| multi-hop | 1 | 0% | 100% |
| procedure | 1 | 0% | 100% |
| numeric | 4 | 12% | 88% |
| unanswerable | 2 | 50% | 100% |

## Manual review of judge verdicts (1 overrides)

| Q | Field | Judge | Manual | Reason |
|---|---|---|---|---|
| 1 | rag_verdict | partial | correct | Manual review: the reference list was truncated by the question author; the extra SMOS listed by RAG (SO, SA, AIMLWF, rApp management) are genuine entries from SMO-ARCH §4.2.1. |

## Base hallucinated, RAG correct (15 cases)

### Q1. What SMO Services (SMOS) does the SMO framework offer?
- **Reference:** SMO Services include RAN NF OAM SMOS, Network Functions Orchestration (NFO) SMOS, Federated O-Cloud Orchestration and Management (FOCOM) SMOS, Service Management and Exposure (SME) SMOS, Data Management and Exposure (DME) SMOS, and Topology Exposure and Inventory (TE&IV) SMOS.
- **Base (incorrect):** The SMO Framework offers the following SMO Services (SMOS):

1. Configuration Management (CM)
2. Lifecycle Management (LM)
3. Performance Management (PM)
4. Fault Management (FM)
5. Security Management (SM)
6. Telemetry Management (TM)
7. Orchestration and Automation (OA)

These SMOS enable the orchestration, automation, and management of O-RAN compliant radio access network components.
  - _Judge:_ The candidate answer lists different SMO Services (SMOS) than those specified in the reference answer.
- **RAG (correct):** The SMO framework offers the following SMO Services (SMOS):

- RAN Network Function OAM (RAN NF OAM) SMOS
- Network Functions Orchestration (NFO) SMOS
- Federated O-Cloud Orchestration and Management (FOCOM) SMOS
- Service Management and Exposure (SME) SMOS
- Data Management and Exposure (DME) SMOS
- Topology Exposure and Inventory Management (TE&IV) SMOS
- Service and Slice Subnet Orchestration (SO) SMOS
- Service and Slice Subnet Assurance (SA) SMOS
- AI/ML workflow (AIMLWF) SMOS
- rApp Management (rApp-Mgmt) SMOS
- A1 Related SMOS (A1Rel-SMOS)
- Software Package Onboarding (SPO) SMOS
- Policy Management and Information (PMI) SMOS [1][2].
- **Cited passage [1]** `O-RAN.WG1.TS.SMO-ARCH-R005-v04.00.docx` §3.1	Terms … §4.2.1	Introduction to SMO Services:
  > terms given in [1] and the following apply: Data Consumer: an entity capable of consuming data originating from other entities. Data Producer: an entity capable of producing data which can be consumed by other entities. Intent: formal specification of all requirements including goals and constraints given to a system NOTE: This definition aligns with the definitions in 3GPP TS 28.312 [i.2], Clause 3.1 and in TMF921 [i.3]. RAN management intent owner: an authorized SMO service consumer, responsible for formulating the RAN management Intents as per its own goals and requirements and [...]

### Q5. What is the R1 interface and what does it enable?
- **Reference:** R1 is the interface between rApps and the SMO/Non-RT RIC framework. It enables multi-vendor rApps to consume or produce R1 services, supports exchange of control signalling and collection/delivery of data, and is independent of specific SMO / Non-RT RIC framework implementations.
- **Base (incorrect):** The R1 interface in O-RAN is the Radio Unit (RU) to Remote Radio Unit (RRU) or Distributed Antenna System (DAS) interface. It enables the separation of the radio frequency (RF) path from the digital signal processing, allowing for flexible and modular design of radio access networks.
  - _Judge:_ The candidate answer describes the R1 interface incorrectly as the RU to RRU or DAS interface, whereas the reference specifies it as the interface between rApps and the SMO/Non-RT RIC framework.
- **RAG (correct):** The R1 interface is an open logical interface within the O-RAN architecture between rApps and the Non-RT RIC framework [1][4]. It enables the exchange of control signaling information and the collection and delivery of data between endpoints [1]. Specifically, the R1 interface:

- Supports the registration and deregistration of R1 services [1][5].
- Enables authentication of rApps [1][4].
- Facilitates authorization of requests to access R1 services [1][4].
- Supports service discovery and service notifications for registered R1 services [1][5].
- Manages the registration and deregistration of DME types [1][5].
- Handles subscriptions and unsubscriptions for registered DME types, as well as the collection and delivery of data for subscribed DME types [1][5].
- Supports functionalities related to A1 and O2 interfaces, RAN OAM, and AI/ML workflows [1][5].

Overall, the R1 interface facilitates inter-connection between rApps and Non-RT RIC framework components from different vendors, providing a level of abstraction that allows rApps to consume or produce R1 services independently of specific implementations [1].
- **Cited passage [1]** `O-RAN.WG2.TS.R1GAP-R005-v14.01.pdf` p.6-8:
  > App instance, assigned by the SMO/Non-RT RIC framework during rApp registration. 3.2 Symbols Void 3.3 Abbreviations For the purposes of the present document, the following abbreviations apply. AI Artificial Intelligence API Application Programming Interface CM Configuration Management DME Data Management and exposure DMS Deployment Management Service EI Enrichment Information FQDN Fully Qualified Domain Name ________________________________________________________________________________________________ © 2026 by the O-RAN ALLIANCE e.V. Your use is subject to the copyright statement on [...]

### Q6. Which interface does an rApp use to access Non-RT RIC framework services, and which interface does the Non-RT RIC use to send policies to the Near-RT RIC?
- **Reference:** rApps use the R1 interface; the Non-RT RIC sends A1 policies to the Near-RT RIC over the A1 interface.
- **Base (incorrect):** An rApp uses the N24 interface to access Non-RT RIC framework services. The Non-RT RIC uses the N35 interface to send policies to the Near-RT RIC.
  - _Judge:_ The candidate answer incorrectly identifies the interfaces as N24 and N35 instead of R1 and A1.
- **RAG (correct):** An rApp uses the R1 interface to access Non-RT RIC framework services [3][4]. The Non-RT RIC uses the A1 interface to send policies to the Near-RT RIC [3][4].
- **Cited passage [3]** `O-RAN.WG11.TR.ZTA-R005-v06.00.docx` §Informative references … §Terms:
  > and Principles” O-RAN.WG6.ASD: “O-RAN Application Service Descriptor specification” Definition of terms, symbols and abbreviations Terms For the purposes of the present document, the following terms apply: A1 interface: interface between Non-RT RIC and Near-RT RIC [i.34] A1 Enrichment information (EI): enrichment information that is collected or derived at SMO/Non-RT RIC either from non-network data sources or from network functions themselves and provided over the A1 interface to be utilized by Near-RT RIC. [i.34] A1 policy: declarative policy expressed using formal statements that [...]

### Q7. What are A1 policies and what is their purpose?
- **Reference:** A1 policies are declarative policies containing statements on policy objectives and policy resources applicable to e.g. UEs and cells. Their purpose is to let the Non-RT RIC guide the Near-RT RIC, and hence the RAN, towards better fulfilment of the RAN intent.
- **Base (incorrect):** A1 policies in O-RAN refer to admission control policies that determine whether a new connection or service can be established based on network resource availability. Their purpose is to ensure efficient use of network resources by controlling the number of active connections and preventing overloading of the network.
  - _Judge:_ The candidate answer describes A1 policies as admission control policies, which contradicts the reference answer that defines them as declarative policies guiding the RIC towards fulfilling RAN intent.
- **RAG (correct):** A1 policies are declarative policies that contain statements on policy objectives and policy resources applicable to entities like UEs and cells [1][3]. Their purpose is to enable the Non-RT RIC function in the SMO to guide the Near-RT RIC function, and thus the RAN, towards better fulfillment of the RAN intent [2].
- **Cited passage [1]** `O-RAN.WG2.TS.A1GAP-R005-v05.04.pdf` p.8-9:
  > The purpose of the A1 policies is to guide the RAN performance towards the overall goal expressed in RAN intent. The A1 policies are declarative policies that contain statements on policy objectives and policy resources applicable to e.g. UEs and cells. The Non-RT RIC can manage the A1 policies based on A1 policy status and feedback information provided by the Near-RT RIC, and on the network status provided over O1. The Non-RT RIC can use the O1 observables to continuously evaluate the impact of the A1 policies towards fulfilment of the RAN intent and based on internal conditions it can [...]

### Q8. Which RIC services can the Near-RT RIC use from an E2 Node?
- **Reference:** REPORT, INSERT, CONTROL, POLICY and QUERY.
- **Base (incorrect):** The Near-RT RIC can use RAN Configuration and Measurement Services from an E2 Node.
  - _Judge:_ The candidate answer lists RAN Configuration and Measurement Services, which are not mentioned in the reference answer.
- **RAG (correct):** The Near-RT RIC can use several RIC services from an E2 Node, including REPORT, INSERT, CONTROL, POLICY, QUERY, and ASSISTANCE [1][3].
- **Cited passage [1]** `O-RAN.WG3.TS.E2GAP-R005-v09.00.pdf` p.10-11:
  > Near-RT RIC; - Enables the Near-RT RIC to control selected RAN functions on the E2 Node. © 2026 by the O-RAN ALLIANCE e.V. Your use is subject to the copyright statement on the cover page of this specification. 11 O-RAN.WG3.TS.E2GAP-R005-v09.00 5.3 Functions of the E2 interface 5.3.1 General The E2 functions are grouped into the following categories: RIC services supported by RIC functional procedures: - RIC Services (REPORT, INSERT, CONTROL, POLICY, QUERY and ASSISTANCE), as described in clause 5.3.2) supported by RIC functional procedures (RIC Subscription, RIC Subscription [...]

### Q9. What are the steps of the E2 REPORT service?
- **Reference:** 1) The Near-RT RIC configures (and may later modify) a RIC Subscription in the E2 Node specifying the Indication (Report) to send on each occurrence of the RIC trigger event; 2) during normal operation of the associated procedure, the E2 Node detects the RIC Event Trigger; 3) after completing previous RIC actions, the E2 Node sends a RIC INDICATION message with the requested REPORT information to the Near-RT RIC, and the associated procedure continues in the E2 Node.
- **Base (incorrect):** The E2 REPORT service in O-RAN involves several steps:

1. **Request Initiation**: The requesting entity (e.g., OAM server) initiates a report request to the reporting entity (e.g., gNB or CU).

2. **Configuration**: The reporting entity configures itself based on the request parameters, such as the type of data to be reported and the frequency.

3. **Data Collection**: The reporting entity collects the required data according to the configuration.

4. **Report Generation**: The collected data is formatted into a report according to predefined templates or structures.

5. **Transmission**: The report is transmitted from the reporting entity to the requesting entity over the E2 interface.

6. **Validation**: The requesting entity validates the received report for accuracy and completeness.

7. **Acknowledgment**: The reporting entity receives an acknowledgment from the requesting entity upon successful receipt and processing of the report.
  - _Judge:_ The candidate answer describes a generic reporting process, while the reference answer specifically outlines the steps of the E2 REPORT service in O-RAN, involving the Near-RT RIC and E2 Node interactions.
- **RAG (correct):** The steps of the E2 REPORT service are as follows:

1. Near-RT RIC configures, and subsequently may modify, a RIC Subscription in the E2 Node with information for Indication (Report) that is to be sent by the E2 Node with each occurrence of RIC trigger event condition [1][2].
2. During normal functioning of an associated procedure in the E2 Node, a RIC Event Trigger is detected.
3. After completing any previous RIC actions, E2 Node sends RIC INDICATION message to Near-RT RIC containing the requested REPORT information along with the originating Request ID.
4. Associated procedure continues in the E2 Node, including any subsequent RIC actions.
- **Cited passage [1]** `O-RAN.WG3.TS.E2GAP-R005-v09.00.pdf` p.10-11:
  > Near-RT RIC; - Enables the Near-RT RIC to control selected RAN functions on the E2 Node. © 2026 by the O-RAN ALLIANCE e.V. Your use is subject to the copyright statement on the cover page of this specification. 11 O-RAN.WG3.TS.E2GAP-R005-v09.00 5.3 Functions of the E2 interface 5.3.1 General The E2 functions are grouped into the following categories: RIC services supported by RIC functional procedures: - RIC Services (REPORT, INSERT, CONTROL, POLICY, QUERY and ASSISTANCE), as described in clause 5.3.2) supported by RIC functional procedures (RIC Subscription, RIC Subscription [...]

### Q10. What latency range must the E2 interface support for near-real-time optimization?
- **Reference:** From 10 milliseconds up to 1 second.
- **Base (incorrect):** The E2 interface in O-RAN must support a latency range of less than 10 milliseconds to enable near-real-time optimization.
  - _Judge:_ The candidate answer states a latency range of less than 10 milliseconds, which contradicts the reference answer's range of 10 milliseconds up to 1 second.
- **RAG (correct):** The E2 interface must support latency requirements for near-real-time optimization, ranging from 10 milliseconds up to 1 second [1].
- **Cited passage [1]** `O-RAN.WG3.TS.E2GAP-R005-v09.00.pdf` p.8-9:
  > E2 Node E2 Near-RT RIC E2 E2 E2 Node O-eNB E2 E1 Open Fronthaul F1-u Figure 4.2-1: O-RAN architecture overview showing Near-RT RIC interfaces With respect to the E2 interface: © 2026 by the O-RAN ALLIANCE e.V. Your use is subject to the copyright statement on the cover page of this specification. 9 O-RAN.WG3.TS.E2GAP-R005-v09.00 - E2 is a logical interface connecting the Near-RT RIC with an E2 Node: - The Near-RT RIC is connected to the O-CU-CP; - The Near-RT RIC is connected to the O-CU-UP; - The Near-RT RIC is connected to the O-DU; - The Near-RT RIC is connected to the O-eNB. - An E2 [...]

### Q11. What RIC Event Trigger styles are defined in E2SM-KPM?
- **Reference:** Style 1 'Periodic Report' (event trigger based on a reporting period) and Style 2 'Measurement Event' (event trigger based on triggering conditions associated with specific subscribed measurements).
- **Base (incorrect):** E2SM-KPM defines three RIC Event Trigger styles: Periodic, Threshold Cross, and Window Average.
  - _Judge:_ The candidate answer lists three event trigger styles, which contradicts the reference that specifies only two styles.
- **RAG (correct):** According to the provided context, the RIC Event Trigger styles defined in E2SM-KPM are:

- **Event Trigger Style 1: Periodic Report** [1][2][3]
- **Event Trigger Style 2: Measurement Event** [1][2][3]

These styles are listed in Table 7.3.1 of the document [1][3].
- **Cited passage [1]** `O-RAN.WG3.TS.E2SM-KPM-R005-v08.00.docx` §7.4.7.3	REPORT Service RIC Indication Header IE contents … §7.9.0	Conversion of measurement definitions:
  > 4.2.3. The Job ID IE shall be included if the Reporting Approach IE is included in this REPORT Service RIC Action Definition IE and set to “Single Integrated”. 7.4.7.4 REPORT Service RIC Indication Message IE contents REPORT Service style 255 shall use the E2SM-KPM Indication Message IE Format 255 (see clause 8.2.1.4.4) if the Reporting Approach IE is included in this REPORT Service RIC Action Definition IE and set to “Single Integrated”. In this case, the message carries a sequence of RIC Indication Message IE for each job identified by the Job ID IE, carrying the job result formatted [...]

### Q14. What is the Y1 interface used for?
- **Reference:** Y1 lets authorized consumers (O-RAN or 3GPP NFs) request and receive RAN Analytics Information (RAI) from the Near-RT RIC (e.g. via RAI query and subscribe/notify services); it is an open, multi-vendor, extensible interface.
- **Base (incorrect):** The Y1 interface in O-RAN is used for the management and control of the Radio Unit (RU) from the Remote Radio Unit (RRU) or Distributed Antenna System (DAS) controller. It enables the separation of the Radio Unit's hardware and software, facilitating remote management and software updates.
  - _Judge:_ The candidate answer describes the Y1 interface as being used for management and control of the Radio Unit, which is incorrect; the reference specifies it is used for RAN Analytics Information exchange between authorized consumers and the Near-RT RIC.
- **RAG (correct):** The Y1 interface is used for inter-connection of Near-RT RIC and Y1 consumers [2][4]. It enables services to be accessed by authorized consumers and supports RAN analytics information services [2]. Consumers can subscribe to or request RAN analytics information through this interface [2][4].
- **Cited passage [2]** `O-RAN.WG3.TS.Y1GAP-R005-v01.02.docx` §3.3	Abbreviations … §5.2.4	RAI_Notify service operation:
  > ] and the following apply: RAI RAN Analytics Information 4 General Aspects 4.1 Reference Model for Y1 interface As depicted in Figure 4.1-1, the O-RAN architecture [1] supports authorized consumers, which may be O-RAN or 3GPP NFs, to request RAN analytics information from Near-RT RIC via Y1 interface. Figure 4.1-1: Reference Model for Y1 interface 4.2 Y1 interface general principles The general principles for the specification of the Y1 interface are as follows: - The Y1 interface is an open logical interface that enables services to be accessed by authorized consumers; - The Y1 [...]

### Q16. Which protocol and data modelling language does the Open Fronthaul M-Plane use to manage the O-RU?
- **Reference:** NETCONF (carried over SSH or TLS) with YANG data models.
- **Base (incorrect):** The Open Fronthaul M-Plane uses gRPC for the protocol and Protocol Buffers (protobuf) as the data modelling language to manage the O-RU.
  - _Judge:_ The candidate answer incorrectly states gRPC and Protocol Buffers as the protocol and data modelling language, whereas the reference specifies NETCONF and YANG.
- **RAG (correct):** The Open Fronthaul M-Plane uses NETCONF as the network element management protocol [1][3] and YANG as the data modelling language [1][3].
- **Cited passage [1]** `O-RAN.WG4.TS.MP.0-R005-v22.00.docx` §5.1.2	M-Plane architecture model … §5.1.3	Transport network:
  > 1.2-1, the hybrid architecture enables one or more direct logical interface(s) between management system(s) and O-RU in addition to a logical interface between O-DU and the O-RU. In the hybrid model, the accounts of the NETCONF clients connecting to the O-RU shall be configured with one or more privilege groups that reflect the NETCONF client's responsibilities, allowing functions like O-RU software management, performance management, configuration management, carrier configuration and fault management to be managed directly by the management system(s). NOTE 1: This avoids the situation [...]

### Q17. What is the D2 interface?
- **Reference:** D2 is the inter-O-DU interface that enables multi-vendor carrier aggregation in NR (between a PCell O-DU and SCell O-DU), with a control plane (D2-c) and user plane (D2-u).
- **Base (incorrect):** The D2 interface is a direct connection between the Radio Unit (RU) and the Digital Unit (DU) in an O-RAN architecture, enabling direct data path communication and reducing latency.
  - _Judge:_ The candidate answer incorrectly describes the D2 interface as a connection between the RU and DU, whereas the reference specifies it as the inter-O-DU interface for multi-vendor carrier aggregation in NR.
- **RAG (correct):** The D2 interface is an inter O-DU interface designed to facilitate multi-vendor carrier aggregation in NR [1][3]. It provides connectivity between O-DUs to support inter O-DU carrier aggregation and is divided into control plane (D2-c) and user plane (D2-u) functionalities [1][2].
- **Cited passage [1]** `O-RAN.WG5.TS.D2GAP.0-R005-v03.00.docx` §4.5	D2 interface capabilities … §5.2.1	Interface management function:
  > CA. 5 Functions of the D2 interface 5.1 General The D2 interface provides connectivity between O-DUs to facilitate inter O-DU carrier aggregation. Its functionality is divided into two parts: control plane (D2-c) and user plane(D2-u). The following clauses describe the functions supported over D2-c and D2-u. 5.2 D2-c function 5.2.1 Interface management function The D2 setup function allows for the initial setup of a D2 connection between two O-DUs, including exchange of the cell-level data. Configuration of the D2 interface endpoints can be managed by the SMO to O-DU via the O1 [...]

### Q18. What is the O2 interface used for?
- **Reference:** O2 is an open logical interface providing secured communication between the SMO and the O-Cloud. It enables management of O-Cloud infrastructure (O2ims) and deployment lifecycle management of cloudified O-RAN NFs running on the O-Cloud (O2dms).
- **Base (incorrect):** The O2 interface in O-RAN is used for remote radio unit (RRU) management, allowing for the control and monitoring of RRU functions from a centralized unit or cloud environment.
  - _Judge:_ The candidate answer incorrectly states that the O2 interface is used for RRU management, whereas the reference specifies it is for communication between the SMO and the O-Cloud for management and deployment lifecycle.
- **RAG (correct):** The O2 interface is used for providing secured communication between the SMO (Service Management and Orchestration) and the O-Cloud. It enables the management of O-Cloud infrastructures and the deployment life cycle management of O-RAN cloudified NFs (Network Functions) that run on the O-Cloud [2][3].
- **Cited passage [2]** `O-RAN.WG6.TS.O2-GA&P-R005-v11.00.pdf` p.8-10:
  > CPUs, Memories, Storages, NICs, HW Accelerators, etc. O-Cloud Node Cluster: a collection of O-Cloud Nodes that work in concert with each other, through a set of interconnecting O-Cloud Node Cluster Site Networks. O-Cloud Platform: a platform comprising hardware and software that provides O-Cloud capabilities and services to execute RAN network functions. 1.3.2 Symbols Void 1.3.3 Abbreviations For the purposes of the present document, the abbreviations [given in [i.1] and the following] apply: NOTE: An abbreviation defined in the present document takes precedence over the definition of [...]

### Q19. In the WG8 O-CU/O-DU reference design, which deployment scenario is used as the example and what carrier bandwidth is supported at L1?
- **Reference:** The indoor pico cell deployment scenario; carrier bandwidth of 100 MHz.
- **Base (incorrect):** In the WG8 O-CU/O-DU reference design, the 4x30MHz carrier bandwidth is used as the example for L1 support. This deployment scenario focuses on a typical 5G network setup with multiple carriers.
  - _Judge:_ The candidate answer contradicts the reference by specifying a 4x30MHz carrier bandwidth instead of the 100 MHz mentioned in the reference.
- **RAG (correct):** In the WG8 O-CU/O-DU reference design, the deployment scenario of indoor pico cell is used as an example [1]. The carrier bandwidth supported at L1 is 100MHz [1].
- **Cited passage [1]** `O-RAN.WG8.TS.AAD.0-R005-v18.00.docx` §Abbreviations … §Requirements:
  > Physical (L1) access layer of RAN PRACH Physical Random Access Channel PRB Physical Resource Block PUCCH Physical Uplink Control Channel PUSCH Physical Uplink Shared Channel PSS Primary Synchronization Signal PTRS Phase Tracking Reference Signal QAM Quadrature Amplitude Modulation QPSK Quadrature (Quaternary) Phase Shift Keying QoS Quality of Service RACH Random Access Channel RAN Radio Access Network Rel-x Release number: where x is the actual release number RF Radio Frequency RLC Radio Link Control protocol RRC Radio Resource Control protocol RU Radio Unit as defined by 3GPP Rx [...]

### Q20. In Xhaul transport, approximately how much delay asymmetry does 7 m of extra standard single-mode fiber introduce?
- **Reference:** About 34 ns.
- **Base (incorrect):** Approximately 1 µs per kilometer of fiber introduces delay asymmetry. Therefore, 7 meters of extra standard single-mode fiber introduces about 7 ns (0.007 µs) of delay asymmetry.
  - _Judge:_ The candidate answer significantly underestimates the delay asymmetry introduced by 7 meters of extra fiber.
- **RAG (correct):** According to the context provided, 7 meters of additional standard single-mode fiber introduces approximately a 34 ns delay [1][10].
- **Cited passage [1]** `O-RAN.WG9.XTRP-REQ.0-R005-v02.00.pdf` p.69-70:
  > a. Performance 1 b. Operation 2 c. Reliability 3 d. Security 4 5 3) TN slice OAM 6 a. Dynamic discovery 7 b. Performance and SLA measurement 8 9 4) Virtualization and abstraction 10 a. Use virtualization technology 11 b. Isolation between slices 12 13 5) Multi-domain 14 a. With other components of the slice 15 b. Between network domains 16 17 Transport engineer’s considerations 18 19 With the introduction of network slicing transport network engineers need to consider: 20 21 1) Concurrent connectivity between: 22 a. WAN to WAN components 23 b. WAN to DC based NFs 24 c. DC based NFs to DC [...]

### Q24. What does the O-RAN Z7 interface connect, and which working group specifies it?
- **Reference:** There is no Z7 interface in O-RAN; the documents do not define it (false premise).
- **Base (incorrect):** The O-RAN Z7 interface connects the Radio Unit (RU) to the Remote Radio Unit (RRU) or Distributed Antenna System (DAS). It is specified by the O-RAN Alliance's Z-WG (Zonal Working Group).
  - _Judge:_ The candidate confidently provides specific information about the Z7 interface, which does not exist in O-RAN specifications.
- **RAG (correct):** The provided documents do not cover this.
- **Cited passage [1]** `O-RAN.WG11.TS.Security-Requirements-Specification.0-R004-v11.00.docx` §Abbreviations … §Introduction:
  > MFA Multi-Factor Authentication mTLS mutual Transport Layer Security NETCONF Network Configuration Protocol NF Network Function NFO Network Function Orchestration O-DU O-RAN Distributed Unit O-RU O-RAN Radio Unit OSC O-RAN Software Community PDCP Packet Data Convergence Protocol PKIX Public-Key Infrastructure using X.509 [81] PNF Physical Network Function PTP Precision Timing Protocol RAN Radio Access Network rAppId rApp Instance Identifier RBAC Role-based Access Control RIC O-RAN RAN Intelligent Controller SBOM Software Bill of Materials SDL Shared Data Layer SDLC Software Development [...]

## RAG not fully correct (5 cases), for the error analysis

- **Q3** (partial, retrieval hit=True): In the O-RAN slicing architecture, what is a NetworkSliceSubnet Instance (NSSI)? | The candidate answer correctly identifies NSSI as a NetworkSliceSubnet MOI but does not mention its specification in 3GPP TS 28.530.
- **Q4** (partial, retrieval hit=False): How do the Non-RT RIC and the Near-RT RIC differ in control loop timescale? | The candidate answer captures the general idea of fast vs. slow loop optimization but does not specify the exact control loop timescales.
- **Q12** (partial, retrieval hit=True): What is E2SM-KPM REPORT Service Style 1 used for? | The candidate answer provides additional details about periodic reporting and the use of RIC Event Trigger Definition IE Format 1, but it does not explicitly mention that Style 1 is used to carry a measurement report from a target E2 Node, which is a key fact in the reference answer.
- **Q21** (partial, retrieval hit=True): What does the O1 Interface Specification define? | The candidate answer focuses on the communication and security aspects between SMO and NFs, but it misses the key fact about the management services (MnS) supported between O1-compliant Managed Elements and the SMO.
- **Q22** (partial, retrieval hit=True): What security protocol must SMO internal communications support for mutual authentication between SMO functions? | The candidate answer correctly mentions mTLS but omits the additional support for TLS with pre-shared key (PSK).
