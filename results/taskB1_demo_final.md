# Task B1: spec Q&A assistant with citations (final system)

Knowledge base: 166 O-RAN specs, 12,042 chunks (800 tokens, 15% overlap) · retrieval: bge-m3 top-30 → bge-reranker-v2-m3 → top-5 · generator: Qwen2.5-7B-Instruct

## Demo 1: How does an xApp subscribe to E2 Node data, and what happens in the Near-RT RIC platform?

**RAG answer:**

An xApp subscribes to E2 Node data through the following steps:

1. The xApp sends a request to the Near-RT RIC platform to subscribe for pushes related to E2NodeList and/or E2NodeInfo [3][5].
2. The Near-RT RIC platform responds to the xApp's subscription request [3][5].
3. When an E2AP Global Procedure (such as E2 Setup, Reset, E2 Removal, RIC Service Update, or E2 Node Configuration Update) is initiated by an E2 Node or the Near-RT RIC, the Near-RT RIC platform updates its database [3][5].
4. The Near-RT RIC platform then triggers an SDL procedure [3][5].
5. The Near-RT RIC platform retrieves a list of xApps that would be interested in this update [3][5].
6. For each relevant xApp, the Near-RT RIC platform sends a push of E2NodeList or E2NodeInfo to the xApp, which includes the E2NodeID [3][5].

These steps ensure that the xApp is informed about any changes to E2 Node information [3][5].

**Cited sources:**

- [3] `O-RAN.WG3.TS.RICARCH-R005-v09.00.docx`, §9.5.8.1       Subscribe/Update-Notify for E2NodeInfo and E2NodeList … §9.5.8.2        Subscribe/Push for E2NodeInfo and E2NodeList (relevance 0.99)
- [5] `O-RAN.WG3.TS.RICARCH-R005-v09.00.docx`, §9.5.8.2       Subscribe/Push for E2NodeInfo and E2NodeList … §9.5.8.3 xApp data sharing for RAN analytics information exposure (relevance 0.99)

**Same model without RAG:**

In the Near-RT RIC (Real-Time RIC) platform, an xApp (Crosshaul Application) subscribes to E2 Node data through the E2 interface. The process involves:

1. **Subscription Request**: The xApp sends a subscription request to the E2 Node via the E2 interface, specifying the type of data it needs.

2. **Data Delivery**: Upon receiving the subscription request, the E2 Node starts delivering the requested data to the xApp in real-time or near-real-time.

3. **Processing**: In the Near-RT RIC platform, the xApp processes this data to make decisions or perform actions based on the network conditions or other parameters.

4. **Feedback Loop**: The xApp can also send commands back to the E2 Node or other components in the RAN (Radio Access Network) to adjust settings or configurations based on the processed data.

This interaction allows for dynamic and efficient management of the radio access network by leveraging real-time data and analytics.

## Demo 2: What is the difference between the Non-RT RIC and the Near-RT RIC in terms of control loop timing and interfaces?

**RAG answer:**

The Non-RT RIC deals with control loops of more than 1 second [1], while the Near-RT RIC handles control loops in the order of 10 ms to 1s [1].

In terms of interfaces:
- The Non-RT RIC logically terminates the A1 interface [3].
- The Near-RT RIC interfaces with E2 Nodes through the E2 interface [1].

**Cited sources:**

- [1] `O-RAN.WG11.TR.Security-Near-RT-RIC-xApps.0-R005-v07.00.docx`, §3.3   Abbreviations … §xApps (relevance 0.99)
- [3] `O-RAN.WG2.TS.Non-RT-RIC-ARCH-R004-v07.00.docx`, §3.3   Abbreviations … §5.1    Requirements for the Non-RT RIC framework (relevance 0.98)

**Same model without RAG:**

Non-RT RIC (Real-Time) has longer control loop timing, typically in seconds or milliseconds, and uses non-real-time interfaces like HTTP/REST for communication. Near-RT RIC has shorter control loop timing, often in milliseconds, and uses real-time interfaces like gRPC or AMQP for faster and more reliable communication.

## Demo 3: What is A1 enrichment information and who provides it?

**RAG answer:**

A1 enrichment information is information provided to an entity, in addition to the information that is generally available to it, in order to enhance the performance of its tasks [1]. It can be produced based on information from one or more sources, such as by relaying, combining, refining, or analyzing information from the input source(s) [2]. According to the context, SMO/Non-RT RIC framework acts as the A1-EI Producer, providing A1 enrichment information to the Near-RT RIC, which takes the role of A1-EI Consumer [2][3].

**Cited sources:**

- [1] `O-RAN.WG2.TS.A1GAP-R005-v05.04.pdf`, p.4-5 (relevance 1.19)
- [2] `O-RAN.WG2.TS.A1GAP-R005-v05.04.pdf`, p.8-9 (relevance 1.18)
- [3] `O-RAN.WG2.TS.A1GAP-R005-v05.04.pdf`, p.14-15 (relevance 1.16)

**Same model without RAG:**

A1 enrichment information enhances the basic A1 measurement results by including additional context such as neighbor cell identities, signal strength predictions, and other useful data. This information is typically provided by the Radio Access Cloud (RAC) or the Radio Cloud Function (RCF) in an O-RAN architecture.

## Demo 4: In the O-RAN AI/ML workflow, what are the ML training host and the ML inference host, and where can they be deployed?

**RAG answer:**

In the O-RAN AI/ML workflow, the ML training host is the network function which hosts the training of the model, including both offline and online training [5]. The ML inference host is the network function which hosts the ML model during inference mode, often coinciding with the Actor [5].

These roles can be deployed in several locations:

- **ML Training Host**: Can be located in the Non-RT RIC [2][3].
- **ML Inference Host**: Typically runs in Near-RT RIC for Loop 2 [3], and in an O-DU for Loop 1 [3].

Additionally, Non-RT RIC can serve as both a training host and a compiling host [5].

**Cited sources:**

- [2] `O-RAN.WG2.AIML-v01.03.pdf`, p.23-24 (relevance 0.99)
- [3] `O-RAN.WG2.AIML-v01.03.pdf`, p.35-37 (relevance 0.99)
- [5] `O-RAN.WG2.AIML-v01.03.pdf`, p.10-11 (relevance 0.98)

**Same model without RAG:**

In the O-RAN AI/ML workflow:
- The ML training host is responsible for training models using large datasets. It can be deployed in centralized cloud environments or at the edge closer to the radio units.
- The ML inference host runs trained models to make real-time decisions. It can be deployed at the edge (e.g., in radio units or small cells) or in centralized cloud/data center environments.

## Demo 5: What does the O-RAN Z7 interface connect, and which working group specifies it?

**RAG answer:**

The provided documents do not cover this.

**Cited sources:**

- _(no citations: the assistant declined)_

**Same model without RAG:**

The O-RAN Z7 interface connects the Radio Unit (RU) to the Remote Radio Unit (RRU) or Distributed Antenna System (DAS). It is specified by the O-RAN Alliance's Z-WG (Zonal Working Group).

