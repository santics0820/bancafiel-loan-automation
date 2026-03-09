from diagrams import Diagram, Cluster, Edge
from diagrams.aws.storage import S3
from diagrams.aws.compute import Lambda
from diagrams.aws.database import RDS
from diagrams.aws.integration import StepFunctions, SNS
from diagrams.aws.network import APIGateway
from diagrams.aws.ml import Bedrock
from diagrams.aws.engagement import SES
from diagrams.aws.general import User

graph_attr = {
    "fontsize": "14",
    "bgcolor": "white",
    "pad": "0.8",
    "splines": "ortho",
    "nodesep": "0.6",
    "ranksep": "0.9",
}

with Diagram(
    "BancaFiel — Loan Processing Architecture",
    filename="/Users/santiagocairesanchez/KPMG/bancafiel_architecture",
    outformat="png",
    show=False,
    direction="LR",
    graph_attr=graph_attr,
):
    client = User("Client")

    with Cluster("Document Ingestion"):
        s3_incoming = S3("S3 Incoming\nBucket")

    with Cluster("Document Intelligence Pipeline"):
        process_doc = Lambda("1. processDocument\n(OCR via Bedrock)")
        bedrock = Bedrock("Claude Sonnet\n(Bedrock)")
        extract_data = Lambda("2. extractData\n(Verify extraction)")
        validate_data = Lambda("3. validateData\n(CURP + customer link)")

    with Cluster("Fraud Detection"):
        detect_fraud = Lambda("4. detectFraud\n(Rule-based scoring)")

    with Cluster("Approval Workflow"):
        step_fn = StepFunctions("Step Functions\nLoan Workflow")
        approval_notifier = Lambda("5. approvalNotifier\n(Analyst email)")

    with Cluster("Decision & Notification"):
        erp_updater = Lambda("6. erpUpdater\n(DB + audit log)")
        notification_sender = Lambda("7. notificationSender\n(Customer email)")
        ses = SES("SES\n(Email)")

    with Cluster("REST API"):
        api_gw = APIGateway("API Gateway")
        api_lambdas = Lambda("API Lambdas\n(list, get, submit\nanalytics, health)")

    with Cluster("Database"):
        rds = RDS("PostgreSQL 15\n(RDS)")

    # Client flow
    client >> api_gw >> api_lambdas
    api_lambdas >> rds

    # Document pipeline
    client >> Edge(label="upload docs") >> s3_incoming
    s3_incoming >> process_doc
    process_doc >> bedrock
    process_doc >> Edge(label="async") >> extract_data
    extract_data >> Edge(label="async") >> validate_data
    validate_data >> Edge(label="async") >> detect_fraud

    # DB reads/writes
    validate_data >> rds
    detect_fraud >> rds

    # Fraud → Step Functions
    detect_fraud >> step_fn
    step_fn >> Edge(label="MEDIUM/LOW") >> approval_notifier
    step_fn >> Edge(label="HIGH → auto-reject") >> erp_updater

    # Approval → ERP → Notification
    approval_notifier >> ses
    approval_notifier >> Edge(label="approve/reject\nAPI call") >> api_gw
    api_gw >> erp_updater
    erp_updater >> rds
    erp_updater >> Edge(label="async") >> notification_sender
    notification_sender >> ses

    # User "received" email
    validate_data >> Edge(label="async", style="dashed") >> notification_sender
