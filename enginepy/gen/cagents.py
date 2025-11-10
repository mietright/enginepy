# pylint: skip-file

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, confloat


class AgentRunCost(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    total_tokens: int | None = Field(
        default=0, description="The total number of tokens used in the agent workflow run", title="Total Tokens"
    )
    total_time: float | None = Field(
        default=0.0, description="The total time taken for the agent workflow run", title="Total Time"
    )
    total_cost: float | None = Field(
        default=0.0, description="The total cost of the agent workflow run", title="Total Cost"
    )


class AgreementReasonEnum(str, Enum):
    AGREED_EXPLICIT = "agreed_explicit"
    AGREED_IMPLICIT_BY_DEFENSE = "agreed_implicit_by_defense"
    AGREED_BY_PLAINTIFF_CONCESSION = "agreed_by_plaintiff_concession"
    DISAGREED_EXPLICIT = "disagreed_explicit"
    DISAGREEMENT_RAISED_BY_DEFENSE = "disagreement_raised_by_defense"
    NOT_MENTIONED = "not_mentioned"
    UNKNOWN = "unknown"


class Annex(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    name: str = Field(..., description="The name of the annex, e.g., 'K1'.", title="Name")
    title: str = Field(..., description="The title of the annex, e.g., 'Rental Contract'.", title="Title")
    description: str = Field(..., description="A brief description of the annex content.", title="Description")


class ArgumentComparisonOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    missing_arguments_in_document_b: list[str] = Field(
        ...,
        description="Arguments present in document version A but missing in document version B.",
        title="Missing Arguments In Document B",
    )
    extra_arguments_in_document_b: list[str] = Field(
        ...,
        description="Arguments present in document version B but not in document version A.",
        title="Extra Arguments In Document B",
    )
    total_missing_arguments: int = Field(
        ..., description="Total number of missing arguments in document version B.", title="Total Missing Arguments"
    )
    total_extra_arguments: int = Field(
        ..., description="Total number of extra arguments found in document version B.", title="Total Extra Arguments"
    )


class BodyRelationtoolAddDocumentsApiWorkflowsRelationtoolWorkflowIdAddDocumentsPost(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    doc_files: list[bytes] = Field(
        ..., description="List of documents to add to the workflow context.", title="Doc Files"
    )
    doc_contents: list[str] | None = Field(
        default=None, description="Text content for the documents.", title="Doc Contents"
    )


class BodyRelationtoolAddMissingDocumentsApiWorkflowsRelationtoolWorkflowIdAddMissingDocumentsPost(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    document_names: list[str] = Field(
        ..., description="List of document names to mark as missing.", title="Document Names"
    )


class BodyRelationtoolEvaluateQualityApiWorkflowsRelationtoolEvaluateQualityPost(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    workflow_id_to_reconcile: str | None = Field(default="", title="Workflow Id To Reconcile")
    case_id: str | None = Field(default="", title="Case Id")
    relation_table_json: str | None = Field(default="", title="Relation Table Json")
    relation_table_file: bytes | None = Field(default=None, title="Relation Table File")
    court_statement_reply_text: str | None = Field(default="", title="Court Statement Reply Text")
    court_statement_reply_file: bytes | None = Field(default=None, title="Court Statement Reply File")
    agent_config_json: str | None = Field(
        default="null",
        description="Dynamic agent configuration as JSON. See DynamicAgentConfig schema.",
        title="Agent Config Json",
    )


class BodyRelationtoolGradeReplyApiWorkflowsRelationtoolGradeReplyPost(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    document_version_b_text: str | None = Field(default="", title="Document Version B Text")
    document_version_b_file: bytes | None = Field(default=None, title="Document Version B File")
    document_version_a_text: str | None = Field(default="", title="Document Version A Text")
    document_version_a_file: bytes | None = Field(default=None, title="Document Version A File")
    workflow_id_for_context: str | None = Field(default=None, title="Workflow Id For Context")
    draft_version: int | None = Field(
        default=None,
        description="Draft version to evaluate by index (supports negative indexing, e.g., -1 for latest). If not provided, uses the latest draft.",
        title="Draft Version",
    )
    relation_table_json: str | None = Field(default="", title="Relation Table Json")
    relation_table_file: bytes | None = Field(default=None, title="Relation Table File")
    statement_of_claim_text: str | None = Field(default="", title="Statement Of Claim Text")
    statement_of_claim_file: bytes | None = Field(default=None, title="Statement Of Claim File")
    statement_of_defense_text: str | None = Field(default="", title="Statement Of Defense Text")
    statement_of_defense_file: bytes | None = Field(default=None, title="Statement Of Defense File")
    other_documents_texts: list[str] | None = Field(default=None, title="Other Documents Texts")
    other_documents_files: list[bytes] | None = Field(default=None, title="Other Documents Files")
    case_summary_text: str | None = Field(default="", title="Case Summary Text")
    case_summary_file: bytes | None = Field(default=None, title="Case Summary File")
    case_timeline_text: str | None = Field(default="", title="Case Timeline Text")
    case_timeline_file: bytes | None = Field(default=None, title="Case Timeline File")
    case_documents_text: str | None = Field(default="", title="Case Documents Text")
    case_documents_file: bytes | None = Field(default=None, title="Case Documents File")
    parallel_models: list[str] | None = Field(
        default=None,
        description="List of models to run evaluations in parallel. If not provided, uses defaults: GPT-4o and Gemini 2.5 Pro. Claude Sonnet 4.5 is currently disabled but can be added explicitly if needed.",
        title="Parallel Models",
    )
    agent_config_json: str | None = Field(
        default="null",
        description="Dynamic agent configuration as JSON. See DynamicAgentConfig schema.",
        title="Agent Config Json",
    )


class BodyRelationtoolRemoveMissingDocumentsApiWorkflowsRelationtoolWorkflowIdRemoveMissingDocumentsPost(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    document_names: list[str] = Field(
        ..., description="List of document names to remove from the missing list.", title="Document Names"
    )


class BodyRunPhotoAnalyzerApiApiWorkflowsPhotoAnalyzerRunPost(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    photo_files: list[bytes] = Field(..., description="List of photos or PDFs to analyze.", title="Photo Files")
    agent_config_json: str | None = Field(
        default="null",
        description='Dynamic agent configuration as a JSON string following DynamicAgentConfig schema. E.g., \'{"model": "gpt-4"}\' or \'{"aliases": {"strong": "gpt-4-turbo"}, "agents": {"PhotoAnalyzerAgent": {"model": "claude-3-opus"}}}}\'.',
        title="Agent Config Json",
    )


class BodyRunRelationToolApiWorkflowsRelationtoolRunPost(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    statement_of_claim_text: str | None = Field(default="", title="Statement Of Claim Text")
    statement_of_claim_file: bytes | None = Field(default=None, title="Statement Of Claim File")
    statement_of_defense_text: str | None = Field(default="", title="Statement Of Defense Text")
    statement_of_defense_file: bytes | None = Field(default=None, title="Statement Of Defense File")
    other_doc_contents: list[str] | None = Field(default=None, title="Other Doc Contents")
    other_doc_files: list[bytes] | None = Field(default=None, title="Other Doc Files")
    documents_not_provided_by_defendant: list[str] | None = Field(
        default=None, title="Documents Not Provided By Defendant"
    )
    reply_example_contents: list[str] | None = Field(default=None, title="Reply Example Contents")
    reply_example_files: list[bytes] | None = Field(default=None, title="Reply Example Files")
    reply_snippet_contents: list[str] | None = Field(default=None, title="Reply Snippet Contents")
    reply_snippet_files: list[bytes] | None = Field(default=None, title="Reply Snippet Files")
    initial_draft_text: str | None = Field(default="", title="Initial Draft Text")
    initial_draft_file: bytes | None = Field(default=None, title="Initial Draft File")
    feedbacks_json: str | None = Field(default="[]", title="Feedbacks Json")
    relationtable_feedbacks_json: str | None = Field(default="[]", title="Relationtable Feedbacks Json")
    agent_config_json: str | None = Field(
        default="null",
        description='Dynamic agent configuration as a JSON string following DynamicAgentConfig schema. E.g., \'{"model": "gpt-4"}\' or \'{"aliases": {"strong": "gpt-4-turbo"}, "agents": {"RelationToolEvidenceAgent": {"model": "claude-3-opus"}}}\'.',
        title="Agent Config Json",
    )
    categories_json: str | None = Field(
        default='{"Badezimmer": [{"name": "Sehr gro\\u00dfes Waschbecken", "is_positive": true, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Besondere und hochwertige Ausstattung", "is_positive": true, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Innen liegendes Badezimmer mit Entl\\u00fcftung", "is_positive": true, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Zweites WC in der Wohnung oder Bad und WC getrennt", "is_positive": true, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Ein gro\\u00dfes Bad", "is_positive": true, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Fu\\u00dfbodenheizung im Bad oder WC", "is_positive": true, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Wandbekleidung und Bodenbelag hochwertig", "is_positive": true, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Wandh\\u00e4ngendes WC mit Sp\\u00fclkasten in der Wand", "is_positive": true, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Strukturheizk\\u00f6rper als Handtuchw\\u00e4rmer", "is_positive": true, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Einhebelmischbatterie (2015)", "is_positive": true, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Von der Badewanne getrennte Dusche", "is_positive": true, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Bodengleiche Dusche (2024)", "is_positive": true, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Nur ein kleines bzw. gar kein Handwaschbecken", "is_positive": false, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "WC ohne L\\u00fcftung", "is_positive": false, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Bad mit Dielenfu\\u00dfboden", "is_positive": false, "description": "Wooden floorboards in the bathroom are considered a negative attribute due to potential water damage.", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Bad oder WC nicht beheizbar oder nur mit Holz-/Kohleheizung oder Elektroheizstrahler", "is_positive": false, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Bad/WC ohne ausreichende Warmwasserversorgung", "is_positive": false, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Nicht modernisiertes Bad mit frei stehender Badewanne ohne separate Dusche", "is_positive": false, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "W\\u00e4nde nicht ausreichend im Spritzwasserbereich von Waschbecken, Badewanne und/oder Dusche", "is_positive": false, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Bad mit WC ohne Fenster", "is_positive": false, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Keine Duschm\\u00f6glichkeit", "is_positive": false, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}, {"name": "Nur ein kleines Bad (kleiner als 4 m\\u00b2)", "is_positive": false, "description": "", "contested": true, "category": "Badezimmer", "value": null, "metadata": {}}], "K\\u00fcche": [{"name": "K\\u00fcchenboden ist aus Fliesen, Linoleum, Feuchtraumlaminat, Parkett oder Terrazzo in gutem Zustand", "is_positive": true, "description": "", "contested": true, "category": "K\\u00fcche", "value": null, "metadata": {}}, {"name": "K\\u00fcche ist ein seperater Raum mit min. 14 m2", "is_positive": true, "description": "", "contested": true, "category": "K\\u00fcche", "value": null, "metadata": {}}, {"name": "Einbauk\\u00fcche mit Ober- und Unterschr\\u00e4nken sowie Herd und Sp\\u00fcle", "is_positive": true, "description": "", "contested": true, "category": "K\\u00fcche", "value": null, "metadata": {}}, {"name": "Ceran oder Induktions-Kochfeld", "is_positive": true, "description": "", "contested": true, "category": "K\\u00fcche", "value": null, "metadata": {}}, {"name": "Dunstabzugshaube", "is_positive": true, "description": "", "contested": true, "category": "K\\u00fcche", "value": null, "metadata": {}}, {"name": "K\\u00fchlschrank", "is_positive": true, "description": "", "contested": true, "category": "K\\u00fcche", "value": null, "metadata": {}}, {"name": "K\\u00fcche ohne Fenster oder Entl\\u00fcftung", "is_positive": false, "description": "", "contested": true, "category": "K\\u00fcche", "value": null, "metadata": {}}, {"name": "Keine Kochm\\u00f6glichkeit in der K\\u00fcche", "is_positive": false, "description": "", "contested": true, "category": "K\\u00fcche", "value": null, "metadata": {}}, {"name": "Keine Sp\\u00fcle in der K\\u00fcche", "is_positive": false, "description": "", "contested": true, "category": "K\\u00fcche", "value": null, "metadata": {}}, {"name": "Keine ausreichende Warmwasserversorgung", "is_positive": false, "description": "", "contested": true, "category": "K\\u00fcche", "value": null, "metadata": {}}, {"name": "K\\u00fcche ist nicht beheizbar oder nur mit Holz-/Kohleheizung", "is_positive": false, "description": "", "contested": true, "category": "K\\u00fcche", "value": null, "metadata": {}}, {"name": "Kein Platz oder kein Anschluss f\\u00fcr Geschirrsp\\u00fcler", "is_positive": false, "description": "", "contested": true, "category": "K\\u00fcche", "value": null, "metadata": {}}], "Wohnung": [{"name": "Einbauschrank oder Abstellraum", "is_positive": true, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "Gro\\u00dfer, ger\\u00e4umiger Balkon, Dachterasse, Loggia oder Wintergarten vorhanden", "is_positive": true, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "\\u00dcberwiegend Fu\\u00dfbodenheizung", "is_positive": true, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "Heizungsrohre \\u00fcberwiegend nicht sichtbar", "is_positive": true, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "Roll\\u00e4den vorhanden", "is_positive": true, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "Wohnungsbezogener Kaltwasserz\\u00e4hler", "is_positive": true, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "Mindestens ein Wohnraum gr\\u00f6\\u00dfer als 40 Quadratmeter", "is_positive": true, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "Wohnung ist barrierearm", "is_positive": true, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "Wohnung in den meisten R\\u00e4umen parkett, Natur, bzw. Kunststeinfliesen oder einen anderen hochwertigen Bodenbelag", "is_positive": true, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "\\u00fcberwiegend W\\u00e4rmeschutzverglasung (Einbau ab 2002) oder Schallschutzfenster", "is_positive": true, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "hochwertige Deckenverkleidung", "is_positive": true, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "\\u00dcberwiegend Einfachverglasung in der Wohnung", "is_positive": false, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "\\u00dcnzureichende Elektroinstallation", "is_positive": false, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "Elektroinstallation \\u00fcberwiegend auf dem Putz sichtbar", "is_positive": false, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "Be- und Entw\\u00e4sserungsinstallation \\u00fcberwiegend auf dem Putz sichtbar", "is_positive": false, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "Kein Platz oder kein Anschluss f\\u00fcr Waschmaschine in K\\u00fcche oder Bad", "is_positive": false, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "Schlechter Schnitt in der Wohnung", "is_positive": false, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}, {"name": "Kein Balkon/Terasse/Loggia/Wintergarten, obwohl rechtlich zul\\u00e4ssig", "is_positive": false, "description": "", "contested": true, "category": "Wohnung", "value": null, "metadata": {}}], "Geb\\u00e4ude": [{"name": "Abschlie\\u00dfbarer leicht zug\\u00e4nglicher Fahrradabstellraum innerhalb des Geb\\u00e4udes oder Abstellpl\\u00e4tze mit Anschlie\\u00dfm\\u00f6glichkeit auf dem Grundst\\u00fcck", "is_positive": true, "description": "", "contested": true, "category": "Geb\\u00e4ude", "value": null, "metadata": {}}, {"name": "Im Geb\\u00e4ude zus\\u00e4tzliche nutzbare R\\u00e4ume au\\u00dferhalb der Wohnung (z.B. Gemeinschaftsraum)", "is_positive": true, "description": "", "contested": true, "category": "Geb\\u00e4ude", "value": null, "metadata": {}}, {"name": "Eingangsbereich/Treppenhaus repr\\u00e4sentativ oder hochwertig saniert", "is_positive": true, "description": "", "contested": true, "category": "Geb\\u00e4ude", "value": null, "metadata": {}}, {"name": "\\u00fcberdurchschnittlicher Instandhaltungszustand des Geb\\u00e4udes", "is_positive": true, "description": "", "contested": true, "category": "Geb\\u00e4ude", "value": null, "metadata": {}}, {"name": "Gegen-/Wechselsprechanlage mit Videokontakt und elektrischem T\\u00fcr\\u00f6ffner", "is_positive": true, "description": "", "contested": true, "category": "Geb\\u00e4ude", "value": null, "metadata": {}}, {"name": "Personenaufzug bei weniger als f\\u00fcnf Obergeschossen", "is_positive": true, "description": "", "contested": true, "category": "Geb\\u00e4ude", "value": null, "metadata": {}}, {"name": "Energieverbrauchswert (kwh/m2)", "is_positive": true, "description": "A lower energy consumption value is considered positive.", "contested": true, "category": "Geb\\u00e4ude", "value": null, "metadata": {}}, {"name": "Wann wurde die Heizananlage eingebaut?", "is_positive": true, "description": "A more recently installed heating system is considered positive.", "contested": true, "category": "Geb\\u00e4ude", "value": null, "metadata": {}}, {"name": "Treppenhaus/Eingangsbereich \\u00fcberwiegend in schlechtem Zustand", "is_positive": false, "description": "", "contested": true, "category": "Geb\\u00e4ude", "value": null, "metadata": {}}, {"name": "Kein Mieterkeller oder Ersatzraum zur alleinigen Nutzung des Mieters vorhanden", "is_positive": false, "description": "", "contested": true, "category": "Geb\\u00e4ude", "value": null, "metadata": {}}, {"name": "Hauseingangst\\u00fcr nicht abschlie\\u00dfbar", "is_positive": false, "description": "", "contested": true, "category": "Geb\\u00e4ude", "value": null, "metadata": {}}, {"name": "Schlechter Instandhaltungszustand", "is_positive": false, "description": "", "contested": true, "category": "Geb\\u00e4ude", "value": null, "metadata": {}}, {"name": "Wohnung liegt im Seitenfl\\u00fcgel oder Quergeb\\u00e4ude bei verdichteter Bebauung", "is_positive": false, "description": "", "contested": true, "category": "Geb\\u00e4ude", "value": null, "metadata": {}}, {"name": "Wohnung ab dem f\\u00fcnften Obergeschoss ohne Personenaufzug", "is_positive": false, "description": "", "contested": true, "category": "Geb\\u00e4ude", "value": null, "metadata": {}}, {"name": "Keine Gegen-/Wechselsprechanlage mit elektrischem T\\u00fcr\\u00f6ffner", "is_positive": false, "description": "", "contested": true, "category": "Geb\\u00e4ude", "value": null, "metadata": {}}], "Wohnumfeld": [{"name": "Bevorzugte Citylage", "is_positive": true, "description": "", "contested": true, "category": "Wohnumfeld", "value": null, "metadata": {}}, {"name": "Besonders ruhige Lage", "is_positive": true, "description": "", "contested": true, "category": "Wohnumfeld", "value": null, "metadata": {}}, {"name": "Aufw\\u00e4ndig gestaltetes Wohnumfeld auf dem Grundst\\u00fcck", "is_positive": true, "description": "", "contested": true, "category": "Wohnumfeld", "value": null, "metadata": {}}, {"name": "Vom Vermieter zur Verf\\u00fcgung gestelltes PKW-Parkplatzangebot in der N\\u00e4he", "is_positive": true, "description": "", "contested": true, "category": "Wohnumfeld", "value": null, "metadata": {}}, {"name": "Garten zur alleinigen Nutzung/Mietergarten ohne Entgelt oder zur Wohnung geh\\u00f6render Garten mit direktem Zugang", "is_positive": true, "description": "", "contested": true, "category": "Wohnumfeld", "value": null, "metadata": {}}, {"name": "Lage in stark vernachl\\u00e4ssigter Umgebung", "is_positive": false, "description": "", "contested": true, "category": "Wohnumfeld", "value": null, "metadata": {}}, {"name": "Besonders l\\u00e4rmbelastete Lage", "is_positive": false, "description": "", "contested": true, "category": "Wohnumfeld", "value": null, "metadata": {}}, {"name": "Besonders geruchsbelastete Lage", "is_positive": false, "description": "", "contested": true, "category": "Wohnumfeld", "value": null, "metadata": {}}, {"name": "Keine Fahrradabstellm\\u00f6glichkeit auf dem Grundst\\u00fcck", "is_positive": false, "description": "", "contested": true, "category": "Wohnumfeld", "value": null, "metadata": {}}]}',
        title="Categories Json",
    )
    topics_json: str | None = Field(default="[]", title="Topics Json")
    to_language: str | None = Field(default="de", title="To Language")
    only_disagreement: bool | None = Field(default=False, title="Only Disagreement")
    include_case_docs: bool | None = Field(default=False, title="Include Case Docs")
    run_document_analysis: bool | None = Field(default=False, title="Run Document Analysis")
    run_legal_analysis: bool | None = Field(default=False, title="Run Legal Analysis")
    run_create_reply: bool | None = Field(default=False, title="Run Create Reply")
    use_reply_examples: bool | None = Field(default=True, title="Use Reply Examples")
    run_timeout_days: int | None = Field(default=3, title="Run Timeout Days")
    metadata_keys: list[str] | None = Field(default=None, title="Metadata Keys")
    metadata_values: list[str] | None = Field(default=None, title="Metadata Values")


class CaseDocAnalysis(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    date: str = Field(..., description="Date of the document", title="Date")
    quote: str = Field(..., description="Quote from the document", title="Quote")
    summary: str = Field(..., description="Summary of the document", title="Summary")
    document_id: str = Field(..., description="ID of the dxocument", title="Document Id")
    document_type: str = Field(
        ..., description="Type of the document, e.g., 'email', 'doc', etc.", title="Document Type"
    )


class CaseDocsAnalysis(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    information: list[CaseDocAnalysis] = Field(
        ..., description="List of document analyses for the case", title="Information"
    )


class CaseRawDataInformation(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    generic: dict[str, Any] | None = Field(default=None, title="Generic")
    hearing_report: dict[str, Any] | None = Field(default=None, title="Hearing Report")
    court_result: dict[str, Any] | None = Field(default=None, title="Court Result")
    rent_index: dict[str, Any] | None = Field(default=None, title="Rent Index")
    kfa: dict[str, Any] | None = Field(default=None, title="KFA")
    kfb: dict[str, Any] | None = Field(default=None, title="KFB")


class ClassificationRentalCtx(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    request_id: int | None = Field(default=-1, title="Request Id")
    document_id: int | None = Field(default=-1, title="Document Id")


class ClassificationRentalType(str, Enum):
    APPROVAL_OF_SETTLEMENT = "approval_of_settlement"
    APPROVAL_OF_SETTLEMENT_COPY = "approval_of_settlement_copy"
    ASSESMENT_OF_COSTS_APPLICATION = "assesment_of_costs_application"
    ASSESMENT_OF_COSTS_DECREE = "assesment_of_costs_decree"
    CESSION = "cession"
    CESSION_COPY = "cession_copy"
    COMPLAINT_BY_TENANT = "complaint_by_tenant"
    COURT_ADVANCE_ON_COSTS = "court_advance_on_costs"
    COURT_ATTACHMENT = "court_attachment"
    COURT_COST_FINAL = "court_cost_final"
    COURT_DOCUMENT = "court_document"
    COURT_ORDER = "court_order"
    COURT_SETTLEMENT = "court_settlement"
    DECREE = "decree"
    DECREE_OF_LITIGATION_VALUE = "decree_of_litigation_value"
    DEFAULT_SUMMONS = "default_summons"
    DELIVERY_FAILURE = "delivery_failure"
    EINIGUNGSANGEBOT_GEGENSEITE = "einigungsangebot_gegenseite"
    ENERGY_CERTIFICATE = "energy_certificate"
    ENFORCEMENT_ORDER = "enforcement_order"
    GENERAL = "general"
    GENERAL_COUNTERPARTY = "general_counterparty"
    GENERAL_COURT = "general_court"
    GENERAL_CUSTOMER = "general_customer"
    INVOICE_MISCELLANEOUS = "invoice_miscellaneous"
    KLAGEENTWURF_AUSKUNFT = "klageentwurf_auskunft"
    LANDLORD_CORRESPONDENCE = "landlord_correspondence"
    LAWSUIT = "lawsuit"
    LEGAL_PROTECTION_INSURANCE_POLICE = "legal_protection_insurance_police"
    MANDATE = "mandate"
    MANDATE_COPY = "mandate_copy"
    MIETENDECKEL_REPAYMENT_REQUEST = "mietendeckel_repayment_request"
    NACHTRAG_GEGENSEITE_UNTERZEICHNET = "nachtrag_gegenseite_unterzeichnet"
    NACHTRAG_KUNDE_UNTERZEICHNET = "nachtrag_kunde_unterzeichnet"
    NOTICE_OF_APPEAL = "notice_of_appeal"
    NOTICE_OF_APPEAL_RESPONSE = "notice_of_appeal_response"
    PFUEB = "pfueb"
    POWER_OF_ATTORNEY = "power_of_attorney"
    PROOF_OF_DELIVERY = "proof_of_delivery"
    PROOF_OF_DELIVERY_COMPLAINT = "proof_of_delivery_complaint"
    PROOF_OF_DELIVERY_COURT = "proof_of_delivery_court"
    PROOF_OF_DELIVERY_CUSTOMER = "proof_of_delivery_customer"
    RENTAL_CONTRACT = "rental_contract"
    RENTAL_CONTRACT_INCOMPLETE = "rental_contract_incomplete"
    RENTAL_CONTRACT_UNSIGNED = "rental_contract_unsigned"
    RENT_INCREASE_LETTER = "rent_increase_letter"
    RETROCESSION = "retrocession"
    RETROCESSION_COPY = "retrocession_copy"
    RSV_CORRESPONDENCE = "rsv_correspondence"
    SENTENCE_FIRST_COURT = "sentence_first_court"
    SENTENCE_SECOND_COURT = "sentence_second_court"
    SITEL_COURT = "sitel_court"
    SITEL_OOC_POST = "sitel_ooc_post"
    STATEMENT = "statement"
    STATEMENT_NOTICE_OF_APPEAL = "statement_notice_of_appeal"
    STATEMENT_OF_DEFENCE = "statement_of_defence"
    STATEMENT_OF_DEFENSE = "statement_of_defense"
    SUMMONS = "summons"
    SUMMONS_CANCELLED = "summons_cancelled"
    SUMMONS_FIRST = "summons_first"
    SUMMONS_RESCHEDULED = "summons_rescheduled"
    TENANT_CORRESPONDENCE = "tenant_correspondence"
    TRANSCRIPT_ORAL_HEARING = "transcript_oral_hearing"
    WIDERRUF_DES_VERGLEICHS = "widerruf_des_vergleichs"
    WIDERRUFSVERGLEICH = "widerrufsvergleich"
    WRITTEN_PRELIMINARY_PROCEEDINGS = "written_preliminary_proceedings"


class Condition(str, Enum):
    LUXURIOUS = "luxurious"
    NORMAL = "normal"
    MINIMAL = "minimal"
    BAD = "bad"


class Mode(str, Enum):
    BYTES = "bytes"
    STRING = "string"
    B64 = "b64"
    URL = "url"


class Content(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    mode: Mode | None = Field(
        default=Mode.STRING,
        description="Mode of the content: 'bytes' for binary data, 'string' for text, 'b64' for base64 encoded data, 'url' for a URL to the content",
        title="Mode",
    )
    mime: str | None = Field(
        default="", description="MIME type of the content, e.g., 'application/pdf' for PDF files", title="Mime"
    )
    content: str | bytes = Field(..., description="Content of the document as a string, bytes or URL", title="Content")
    title: str | None = Field(default="", description="Title of the document", title="Title")


class CriterionGrade(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    grade: confloat(ge=0.0, le=10.0) = Field(..., title="Grade")
    reasoning: str = Field(..., title="Reasoning")


class ExteriorKeyword(str, Enum):
    EXTERIOR = "exterior"
    STAIRWELL = "stairwell"
    CORRIDOR = "corridor"
    BASEMENT = "basement"
    CELLAR = "cellar"


class FeaturesConfig(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    general_features: list[str] | None = Field(
        default=None, description="A list of general features to look for across all photos.", title="General Features"
    )
    room_features: dict[str, list[str]] | None = Field(
        default=None,
        description="A dictionary mapping location names to specific features to look for in those locations.",
        title="Room Features",
    )


class Importance(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FeedbackItem(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    feedback: str = Field(..., description="The specific, actionable feedback.", title="Feedback")
    importance: Importance = Field(..., description="The importance of the feedback for the grade.", title="Importance")


class FormalProceduralComplianceGrade(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    grade: confloat(ge=0.0, le=10.0) = Field(..., title="Grade")
    reasoning: str = Field(..., title="Reasoning")
    formatting_and_citation: CriterionGrade
    procedural_correctness: CriterionGrade


class Job(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    uuid: str = Field(..., title="Uuid")
    name: str = Field(..., title="Name")
    status: str | None = Field(default=None, title="Status")
    result: dict[str, Any] | None = Field(default={}, title="Result")


class JobList(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    jobs: list[Job] | None = Field(default=[], title="Jobs")


class LegalFactualFoundationGrade(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    grade: confloat(ge=0.0, le=10.0) = Field(..., title="Grade")
    reasoning: str = Field(..., title="Reasoning")
    legal_accuracy: CriterionGrade
    factual_correctness: CriterionGrade
    completeness_of_claim: CriterionGrade


class MCPToolChoice(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    server_label: str = Field(..., title="Server Label")
    name: str = Field(..., title="Name")


class MissingDocument(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    document_name: str = Field(
        ..., description="The name or description of the missing document.", title="Document Name"
    )
    reason_for_request: str = Field(
        ...,
        description="Explanation of why this document is needed and how it could affect the draft.",
        title="Reason For Request",
    )
    mentioned_by: str | None = Field(
        default="defendant", description="Who mentioned the document (e.g., 'defendant').", title="Mentioned By"
    )


class Client(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    LITELLM = "litellm"


class ApiMode(str, Enum):
    CHAT = "chat"
    RESPONSE = "response"


class ToolChoice(str, Enum):
    AUTO = "auto"
    REQUIRED = "required"
    NONE = "none"


class Truncation(str, Enum):
    AUTO = "auto"
    DISABLED = "disabled"


class Verbosity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ResponseInclude(str, Enum):
    FILE_SEARCH_CALL_RESULTS = "file_search_call.results"
    WEB_SEARCH_CALL_RESULTS = "web_search_call.results"
    WEB_SEARCH_CALL_ACTION_SOURCES = "web_search_call.action.sources"
    MESSAGE_INPUT_IMAGE_IMAGE_URL = "message.input_image.image_url"
    COMPUTER_CALL_OUTPUT_OUTPUT_IMAGE_URL = "computer_call_output.output.image_url"
    CODE_INTERPRETER_CALL_OUTPUTS = "code_interpreter_call.outputs"
    REASONING_ENCRYPTED_CONTENT = "reasoning.encrypted_content"
    MESSAGE_OUTPUT_TEXT_LOGPROBS = "message.output_text.logprobs"


class OutputFormatEnum(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"


class PersuasionProfessionalismGrade(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    grade: confloat(ge=0.0, le=10.0) = Field(..., title="Grade")
    reasoning: str = Field(..., title="Reasoning")
    clarity_and_precision: CriterionGrade
    professional_tone: CriterionGrade
    structure_and_readability: CriterionGrade


class PhotoAnalyzerRunResponse(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    workflow_id: str = Field(..., title="Workflow Id")
    status_url: str = Field(..., title="Status Url")
    download_url_full: str = Field(..., title="Download Url Full")
    download_url_concise: str = Field(..., title="Download Url Concise")
    download_url_minimal: str = Field(..., title="Download Url Minimal")


class PhotoAnalyzerWorkflowInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    photos: list[Content] = Field(
        ..., description="A list of photos to be analyzed. Each can be an image or a PDF.", title="Photos"
    )
    conditions: list[Condition] | None = Field(
        default=[Condition.LUXURIOUS, Condition.NORMAL, Condition.MINIMAL, Condition.BAD],
        description="A list of possible conditions to assess.",
        title="Conditions",
    )
    exterior_keywords: list[ExteriorKeyword] | None = Field(
        default=[
            ExteriorKeyword.EXTERIOR,
            ExteriorKeyword.STAIRWELL,
            ExteriorKeyword.CORRIDOR,
            ExteriorKeyword.BASEMENT,
            ExteriorKeyword.CELLAR,
        ],
        description="Keywords to identify exterior or common area photos.",
        title="Exterior Keywords",
    )
    features_config: FeaturesConfig | None = Field(default=None, description="Specific features to guide the analysis.")


class PhotoSummaryOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    overall_description: str = Field(
        ...,
        description="A short, engaging description of the property for a potential buyer.",
        title="Overall Description",
    )
    consolidated_building_year: str = Field(
        ...,
        description="The consolidated estimated building year based on all available data.",
        title="Consolidated Building Year",
    )
    overall_condition: str = Field(..., description="The overall condition of the property.", title="Overall Condition")
    key_features: list[str] | None = Field(
        default=None,
        description="A bullet-point list of the most important features of the property.",
        title="Key Features",
    )


class Effort(str, Enum):
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GenerateSummary(str, Enum):
    AUTO = "auto"
    CONCISE = "concise"
    DETAILED = "detailed"


class Summary1(str, Enum):
    AUTO = "auto"
    CONCISE = "concise"
    DETAILED = "detailed"


class Reasoning(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    effort: Effort | None = Field(default=None, title="Effort")
    generate_summary: GenerateSummary | None = Field(default=None, title="Generate Summary")
    summary: Summary1 | None = Field(default=None, title="Summary")


class RelationToolTableRow(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    category: str = Field(..., description="Category of the attribute", title="Category")
    attribute: str = Field(..., description="Name of the attribute", title="Attribute")
    document_a_value: str = Field(..., description="Value of the attribute in the document A", title="Document A Value")
    quote_a: str = Field(..., description="Quote from the document A supporting the attribute", title="Quote A")
    document_b_value: str = Field(..., description="Value of the attribute in the document B", title="Document B Value")
    quote_b: str = Field(..., description="Quote from the document B supporting the attribute", title="Quote B")
    evidence_provided_b: bool = Field(
        ..., description="Whether there is evidence in document B for the attribute", title="Evidence Provided B"
    )
    evidence_b: str = Field(..., description="Evidence supporting the attribute in the document B", title="Evidence B")
    evidence_quote_b: str = Field(
        ..., description="Quote from the document B supporting the attribute", title="Evidence Quote B"
    )
    reasoning: str = Field(
        ..., description="Reasoning for the status of disagreement/agreement of the attribute", title="Reasoning"
    )
    agreement_status: bool = Field(
        ..., description="Status of the attribute: True if agree, FAlse otherwise", title="Agreement Status"
    )
    agreement_reason: AgreementReasonEnum = Field(..., description="The detailed reason for the agreement status.")


class ReplySnippet(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    title: str = Field(..., description="Title of the reply snippet", title="Title")
    short_description: str = Field(..., description="Explain what it's about", title="Short Description")
    text: str = Field(..., description="Text of the snippet", title="Text")


class SourceType(str, Enum):
    URI = "uri"
    BASE64 = "base64"


class SummaryResponseOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    timeline: str = Field(..., title="Timeline")
    summary: str = Field(..., title="Summary")
    summary_changes: list[str] | None = Field(..., title="Summary Changes")
    timeline_changes: list[str] | None = Field(..., title="Timeline Changes")
    last_document_id: str | None = Field(..., title="Last Document Id")
    last_document_date: str | None = Field(..., title="Last Document Date")


class SummaryStatus(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    status: dict[str, Any] = Field(..., title="Status")
    summaries: list[SummaryResponseOutput] = Field(..., title="Summaries")


class TextSummarizerWorkflowContext(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    content: str = Field(..., title="Content")
    feedbacks: list[str] | None = Field(
        default=None, description="List of feedbacks for creating the less verbose text", title="Feedbacks"
    )
    to_language: str | None = Field(
        default="de",
        description="The language to translate the summary to. E.g., 'en' for English, 'de' for German.",
        title="To Language",
    )


class Topic(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    title: str = Field(..., description="The title of the topic to look for.", title="Title")
    description: str = Field(..., description="A short description of the topic.", title="Description")


class ValidationError(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    loc: list[str | int] = Field(..., title="Location")
    msg: str = Field(..., title="Message")
    type: str = Field(..., title="Error Type")


class VersionResp(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    version: str = Field(..., title="Version")


class WithContentMode(str, Enum):
    FULL = "full"
    CHUNK = "chunk"
    SUMMARY = "summary"
    NONE = "none"


class WorkflowInfo(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    name: str | None = Field(default="", description="The name of the agent workflow to run", title="Name")
    wid: str | None = Field(default="", description="The ID of the agent workflow to run", title="Wid")
    run_id: str | None = Field(default="", description="The ID of the agent workflow run", title="Run Id")
    namespace: str | None = Field(default="", description="The namespace of the agent workflow run", title="Namespace")


class WorkflowStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CagentsAgentsConnyCaseSummaryModelsSummaryResponse(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    timeline: str = Field(..., title="Timeline")
    summary: str = Field(..., title="Summary")
    summary_changes: list[str] | None = Field(..., title="Summary Changes")
    timeline_changes: list[str] | None = Field(..., title="Timeline Changes")
    last_document_id: str | None = Field(..., title="Last Document Id")
    last_document_date: str | None = Field(..., title="Last Document Date")


class CagentsAgentsRelationtoolModelsRelationToolAttribute(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    name: str = Field(..., description="Name of the attribute", title="Name")
    is_positive: bool = Field(
        ...,
        description="Whether the attribute is considered a positive aspect (True) or a negative aspect (False)",
        title="Is Positive",
    )
    description: str | None = Field(default="", description="Description of the attribute", title="Description")
    contested: bool | None = Field(
        default=True, description="Whether the attribute is contested (True) or not (False)", title="Contested"
    )
    category: str | None = Field(default="", description="Category to which the attribute belongs", title="Category")
    value: str | bool | int | float | None = Field(default=None, description="Value of the attribute", title="Value")
    metadata: dict[str, str] | None = Field(default=None, description="Metadata for the attribute", title="Metadata")


class EnginepyModelsRelationToolAttribute(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    is_positive: bool | None = Field(
        default=None,
        description="Whether the attribute is considered a positive aspect (True) or a negative aspect (False)",
        title="Is Positive",
    )
    description: str | None = Field(default="", description="Description of the attribute", title="Description")
    contested: bool | None = Field(
        default=True, description="Whether the attribute is contested (True) or not (False)", title="Contested"
    )
    value: str | bool | int | float | None = Field(default=None, description="Value of the attribute", title="Value")
    metadata: dict[str, str] | None = Field(default=None, description="Metadata for the attribute", title="Metadata")
    name: str = Field(..., description="Name of the attribute", title="Name")


class EnginepyModelsSummaryResponse(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    timeline: str | None = Field(default="", title="Timeline")
    summary: str | None = Field(default="", title="Summary")
    summary_changes: list[str] | None = Field(default=None, title="Summary Changes")
    timeline_changes: list[str] | None = Field(default=None, title="Timeline Changes")
    last_document_id: str | None = Field(default=None, title="Last Document Id")
    last_document_date: str | None = Field(default=None, title="Last Document Date")


class AgentInputClassificationRentalCtx(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    context: ClassificationRentalCtx = Field(..., description="The input data for the agent")
    llm_input: str | None = Field(default="", description="The LLM input string for the agent", title="Llm Input")


class AgentInputPhotoAnalyzerWorkflowInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    context: PhotoAnalyzerWorkflowInput = Field(..., description="The input data for the agent")
    llm_input: str | None = Field(default="", description="The LLM input string for the agent", title="Llm Input")


class AgentInputTextSummarizerWorkflowContext(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    context: TextSummarizerWorkflowContext = Field(..., description="The input data for the agent")
    llm_input: str | None = Field(default="", description="The LLM input string for the agent", title="Llm Input")


class ArgumentationStrategyGrade(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    grade: confloat(ge=0.0, le=10.0) = Field(..., title="Grade")
    reasoning: str = Field(..., title="Reasoning")
    logical_coherence: CriterionGrade
    rebuttal_of_opponent: CriterionGrade
    strategic_initiative: CriterionGrade


class AsyncResponseInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    payload: JobList | None = Field(default_factory=lambda: JobList.model_validate({"jobs": []}))
    signature: str | None = Field(default=None, title="Signature")


class AsyncResponseOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    payload: JobList | None = Field(default_factory=lambda: JobList.model_validate({"jobs": []}))
    signature: str | None = Field(default=None, title="Signature")


class ClassificationRentalScore(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    category: ClassificationRentalType
    reasoning: str = Field(..., title="Reasoning")
    confidence_score: float = Field(..., title="Confidence Score")


class ConnyRequestSummaryCtx(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    request_id: int = Field(..., title="Request Id")
    limit: int | None = Field(default=400, title="Limit")
    previous: CagentsAgentsConnyCaseSummaryModelsSummaryResponse | None = None
    retrieved_all: bool | None = Field(default=False, title="Retrieved All")
    mode: WithContentMode | None = WithContentMode.SUMMARY
    output: OutputFormatEnum | None = OutputFormatEnum.JSON
    last_document_id: str | None = Field(default="", title="Last Document Id")
    last_document_date: str | None = Field(default="", title="Last Document Date")


class CreateReplyOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    draft_id: str = Field(
        ..., description="Unique identifier for this draft, including a version suffix (e.g., '_v1').", title="Draft Id"
    )
    refined_from_draft_id: str | None = Field(
        default=None,
        description="The ID of the draft this version was refined from, establishing a lineage.",
        title="Refined From Draft Id",
    )
    creator_model: str | None = Field(
        default=None, description="The specific model used to create this draft (e.g., 'gpt-5').", title="Creator Model"
    )
    is_refined: bool | None = Field(
        default=False, description="True if this draft is a refinement of a previous one.", title="Is Refined"
    )
    summary: str = Field(
        ..., description="A brief, high-level summary of the drafted reply's strategy.", title="Summary"
    )
    reasoning: str = Field(
        ..., description="Detailed explanation of the key strategic choices made in the draft.", title="Reasoning"
    )
    reviewer_instructions: str = Field(
        ..., description="Specific points for the reviewing lawyer to double-check.", title="Reviewer Instructions"
    )
    annexes: list[Annex] = Field(..., description="A complete list of all annexes used in the reply.", title="Annexes")
    missing_documents: list[MissingDocument] | None = Field(
        default=None,
        description="List of documents mentioned by the counterparty but not provided, which could improve the draft.",
        title="Missing Documents",
    )
    reply_draft: str = Field(
        ..., description="The full, complete Replik draft in Markdown format.", title="Reply Draft"
    )


class DetailedGradeInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    legal_factual_foundation: LegalFactualFoundationGrade
    argumentation_strategy: ArgumentationStrategyGrade
    persuasion_professionalism: PersuasionProfessionalismGrade
    formal_procedural_compliance: FormalProceduralComplianceGrade


class DetailedGradeOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    legal_factual_foundation: LegalFactualFoundationGrade
    argumentation_strategy: ArgumentationStrategyGrade
    persuasion_professionalism: PersuasionProfessionalismGrade
    formal_procedural_compliance: FormalProceduralComplianceGrade


class HTTPValidationError(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    detail: list[ValidationError] | None = Field(default=None, title="Detail")


class IndividualGradeOutputInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    grades: DetailedGradeInput | None = None
    feedbacks: list[FeedbackItem] = Field(..., title="Feedbacks")
    overall_reasoning: str = Field(..., title="Overall Reasoning")
    summary_reasoning: str = Field(..., title="Summary Reasoning")
    overall_grade: confloat(ge=0.0, le=10.0) = Field(..., title="Overall Grade")


class IndividualGradeOutputOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    grades: DetailedGradeOutput | None = None
    feedbacks: list[FeedbackItem] = Field(..., title="Feedbacks")
    overall_reasoning: str = Field(..., title="Overall Reasoning")
    summary_reasoning: str = Field(..., title="Summary Reasoning")
    overall_grade: confloat(ge=0.0, le=10.0) = Field(..., title="Overall Grade")


class ModelSettings(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    temperature: float | None = Field(default=None, title="Temperature")
    top_p: float | None = Field(default=None, title="Top P")
    frequency_penalty: float | None = Field(default=None, title="Frequency Penalty")
    presence_penalty: float | None = Field(default=None, title="Presence Penalty")
    tool_choice: ToolChoice | str | MCPToolChoice | None = Field(default=None, title="Tool Choice")
    parallel_tool_calls: bool | None = Field(default=None, title="Parallel Tool Calls")
    truncation: Truncation | None = Field(default=None, title="Truncation")
    max_tokens: int | None = Field(default=None, title="Max Tokens")
    reasoning: Reasoning | None = None
    verbosity: Verbosity | None = Field(default=None, title="Verbosity")
    metadata: dict[str, str] | None = Field(default=None, title="Metadata")
    store: bool | None = Field(default=None, title="Store")
    include_usage: bool | None = Field(default=None, title="Include Usage")
    response_include: list[ResponseInclude | str] | None = Field(default=None, title="Response Include")
    top_logprobs: int | None = Field(default=None, title="Top Logprobs")
    extra_query: dict[str, Any] | None = Field(default=None, title="Extra Query")
    extra_body: Any = Field(default=None, title="Extra Body")
    extra_headers: dict[str, str | None] | None = Field(default=None, title="Extra Headers")
    extra_args: dict[str, Any] | None = Field(default=None, title="Extra Args")


class PhotoSource(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    filename: str = Field(
        ..., description="The original filename of the source file (e.g., 'document.pdf').", title="Filename"
    )
    page_number: int | None = Field(
        default=None, description="The page number if the source is from a PDF.", title="Page Number"
    )
    original_uri: str | None = Field(
        default=None, description="The original S3 URI of the file, if applicable.", title="Original Uri"
    )
    original_content_b64: str | None = Field(
        default=None, description="The original content in base64, if provided directly.", title="Original Content B64"
    )
    original_mime_type: str | None = Field(
        default=None, description="The MIME type of the original file.", title="Original Mime Type"
    )
    split_photo_uri: str | None = Field(
        default=None, description="The S3 URI of the image extracted from a PDF page.", title="Split Photo Uri"
    )
    mime_type: str | None = Field(
        default=None, description="The MIME type of the processed file (e.g., the extracted image).", title="Mime Type"
    )
    source_type: SourceType | None = Field(default=None, description="The type of the original source (uri or base64).")


class RelationToolEvaluateQualityInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    relation_table: list[RelationToolTableRow] = Field(
        ..., description="The relation table output from the evidence agent.", title="Relation Table"
    )
    court_statement_reply: Content = Field(..., description="The court statement reply written by the lawyer.")
    workflow_id_to_reconcile: str | None = Field(
        default="",
        description="The workflow ID of the relation tool run being reconciled.",
        title="Workflow Id To Reconcile",
    )
    case_id: str | None = Field(default=None, description="The case ID, if available.", title="Case Id")


class RelationToolOutputInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    relation_table: list[RelationToolTableRow] = Field(
        ...,
        description="A list of table rows with the comparison between the entities in the claim and defense",
        title="Relation Table",
    )


class RelationToolOutputOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    relation_table: list[RelationToolTableRow] = Field(
        ...,
        description="A list of table rows with the comparison between the entities in the claim and defense",
        title="Relation Table",
    )


class ReplyGradeOutputBaseInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    evaluation_workflow_id: str | None = Field(default=None, title="Evaluation Workflow Id")
    iteration: int | None = Field(default=None, title="Iteration")
    draft_id: str | None = Field(default=None, title="Draft Id")
    evaluator_model: str | None = Field(default=None, title="Evaluator Model")
    document_version_a_grade: IndividualGradeOutputInput | None = None
    document_version_b_grade: IndividualGradeOutputInput
    comparison: ArgumentComparisonOutput | None = None


class ReplyGradeOutputBaseOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    evaluation_workflow_id: str | None = Field(default=None, title="Evaluation Workflow Id")
    iteration: int | None = Field(default=None, title="Iteration")
    draft_id: str | None = Field(default=None, title="Draft Id")
    evaluator_model: str | None = Field(default=None, title="Evaluator Model")
    document_version_a_grade: IndividualGradeOutputOutput | None = None
    document_version_b_grade: IndividualGradeOutputOutput
    comparison: ArgumentComparisonOutput | None = None


class Summary(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    summary_type: str = Field(..., title="Summary Type")
    payload: EnginepyModelsSummaryResponse = Field(..., title="Payload")


class WorkflowStepInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    id: str | None = Field(default="", title="Id")
    name: str | None = Field(default="", description="The name of the workflow step", title="Name")
    status: WorkflowStepStatus | None = WorkflowStepStatus.PENDING
    start_time: AwareDatetime | None = Field(default=None, title="Start Time")
    end_time: AwareDatetime | None = Field(default=None, title="End Time")
    children: list[WorkflowStepInput] | None = Field(default=None, title="Children")
    metadata: dict[str, str] | None = Field(default=None, title="Metadata")


class WorkflowStepOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    id: str | None = Field(default="", title="Id")
    name: str | None = Field(default="", description="The name of the workflow step", title="Name")
    status: WorkflowStepStatus | None = WorkflowStepStatus.PENDING
    start_time: AwareDatetime | None = Field(default=None, title="Start Time")
    end_time: AwareDatetime | None = Field(default=None, title="End Time")
    children: list[WorkflowStepOutput] | None = Field(default=None, title="Children")
    metadata: dict[str, str] | None = Field(default=None, title="Metadata")


class AgentInputConnyRequestSummaryCtx(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    context: ConnyRequestSummaryCtx = Field(..., description="The input data for the agent")
    llm_input: str | None = Field(default="", description="The LLM input string for the agent", title="Llm Input")


class AgentInputRelationToolEvaluateQualityInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    context: RelationToolEvaluateQualityInput = Field(..., description="The input data for the agent")
    llm_input: str | None = Field(default="", description="The LLM input string for the agent", title="Llm Input")


class CaseRawData(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    address: dict[str, Any] | None = Field(default=None, title="Address")
    user: dict[str, Any] | None = Field(default=None, title="User")
    contact: dict[str, Any] | None = Field(default=None, title="Contact")
    court_data: list[dict[str, Any]] | dict[str, Any] | None = Field(default=None, title="Court Data")
    counterparties: list[dict[str, Any]] | None = Field(default=None, title="Counterparties")
    information: CaseRawDataInformation | None = Field(default=None, title="Information")
    summaries: list[Summary] | None = Field(default=None, title="Summaries")
    attributes: dict[str, list[EnginepyModelsRelationToolAttribute]] | None = Field(
        default=None,
        description="Dictionary of attributes with categories as keys and lists of attributes as values",
        title="Attributes",
    )


class ClassificationRentalResponseInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    classification: ClassificationRentalScore
    next_3_potential_categories: list[ClassificationRentalScore] | None = Field(
        default=None, title="Next 3 Potential Categories"
    )


class ClassificationRentalResponseOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    classification: ClassificationRentalScore
    next_categories: list[ClassificationRentalScore] | None = Field(default=None, title="Next Categories")


class ModelInfo(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    model: str | None = Field(default="openai/gpt-4o", title="Model")
    client: Client | None = Field(default=Client.OPENAI, title="Client")
    api_mode: ApiMode | None = Field(default=ApiMode.CHAT, title="Api Mode")
    model_settings: ModelSettings | None = None
    max_input_tokens: int | None = Field(default=None, title="Max Input Tokens")
    base_url: str | None = Field(default=None, title="Base Url")
    api_key: str | None = Field(default=None, title="Api Key")


class PhotoAnalysis(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    source: PhotoSource = Field(..., description="Detailed source information for the photo.")
    location: str = Field(
        ...,
        description="The location depicted in the photo (e.g., Kitchen, Bathroom, Building Exterior).",
        title="Location",
    )
    condition: Condition = Field(..., description="The assessed condition of the location.")
    features: list[str] | None = Field(
        default=None,
        description="A list of identified features (e.g., bathtub, wooden floor, high ceiling).",
        title="Features",
    )
    estimated_building_year: str | None = Field(
        default=None,
        description="The estimated construction year of the building, if applicable.",
        title="Estimated Building Year",
    )
    reasoning: str | None = Field(
        default="",
        description="Reasoning behind the analysis, especially for condition and year estimation.",
        title="Reasoning",
    )


class ReplyGradeOutputInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    evaluation_workflow_id: str | None = Field(default=None, title="Evaluation Workflow Id")
    iteration: int | None = Field(default=None, title="Iteration")
    draft_id: str | None = Field(default=None, title="Draft Id")
    evaluator_model: str | None = Field(default=None, title="Evaluator Model")
    document_version_a_grade: IndividualGradeOutputInput | None = None
    document_version_b_grade: IndividualGradeOutputInput
    comparison: ArgumentComparisonOutput | None = None
    original_evaluations: list[ReplyGradeOutputBaseInput] | None = Field(default=None, title="Original Evaluations")


class ReplyGradeOutputOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    evaluation_workflow_id: str | None = Field(default=None, title="Evaluation Workflow Id")
    iteration: int | None = Field(default=None, title="Iteration")
    draft_id: str | None = Field(default=None, title="Draft Id")
    evaluator_model: str | None = Field(default=None, title="Evaluator Model")
    document_version_a_grade: IndividualGradeOutputOutput | None = None
    document_version_b_grade: IndividualGradeOutputOutput
    comparison: ArgumentComparisonOutput | None = None
    original_evaluations: list[ReplyGradeOutputBaseOutput] | None = Field(default=None, title="Original Evaluations")


class RoomAnalysisOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    photos: list[PhotoAnalysis] | None = Field(
        default=None, description="A list of analyses for photos of this location.", title="Photos"
    )
    combined_features: list[str] | None = Field(
        default=None,
        description="A combined list of unique features observed across all photos of this location.",
        title="Combined Features",
    )
    overall_condition: str = Field(
        ..., description="The overall assessed condition of the room.", title="Overall Condition"
    )
    reasoning: str = Field(
        ..., description="Summary reasoning for the overall condition assessment.", title="Reasoning"
    )
    estimated_building_year: str = Field(
        ...,
        description="Overall estimated building year for the property, if applicable.",
        title="Estimated Building Year",
    )
    location: str | None = Field(
        default="Unknown",
        description="The location name for this room analysis (e.g., 'Kitchen', 'Bathroom 1').",
        title="Location",
    )


class VisibilityInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    steps: WorkflowStepInput | None = Field(default=None, description="The steps in the workflow execution graph")
    trace_id: str | None = Field(
        default="",
        description="The trace ID for the workflow execution, used for tracing and debugging",
        title="Trace Id",
    )
    group_id: str | None = Field(
        default="",
        description="The session ID for the workflow execution, used for session management",
        title="Group Id",
    )


class VisibilityOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    steps: WorkflowStepOutput | None = Field(default=None, description="The steps in the workflow execution graph")
    trace_id: str | None = Field(
        default="",
        description="The trace ID for the workflow execution, used for tracing and debugging",
        title="Trace Id",
    )
    group_id: str | None = Field(
        default="",
        description="The session ID for the workflow execution, used for session management",
        title="Group Id",
    )


class AgentCaseSummaryWorkflowOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    result: list[SummaryResponseOutput] | None = Field(
        ..., description="The output data from the agent workflow", title="Result"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="The metadata for the agent workflow run", title="Metadata"
    )
    cost: AgentRunCost | None = Field(default=None, description="The cost of the agent workflow run")
    workflow_info: WorkflowInfo | None = Field(default=None, description="The information about the agent workflow run")
    visibility: VisibilityOutput | None = Field(
        default=None, description="The visibility information for the agent workflow run"
    )


class AgentClassifierWorkflowOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    result: ClassificationRentalResponseOutput | None = Field(
        ..., description="The output data from the agent workflow"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="The metadata for the agent workflow run", title="Metadata"
    )
    cost: AgentRunCost | None = Field(default=None, description="The cost of the agent workflow run")
    workflow_info: WorkflowInfo | None = Field(default=None, description="The information about the agent workflow run")
    visibility: VisibilityOutput | None = Field(
        default=None, description="The visibility information for the agent workflow run"
    )


class AgentRelationToolWorkflowOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    result: RelationToolOutputOutput | None = Field(..., description="The output data from the agent workflow")
    metadata: dict[str, Any] | None = Field(
        default=None, description="The metadata for the agent workflow run", title="Metadata"
    )
    cost: AgentRunCost | None = Field(default=None, description="The cost of the agent workflow run")
    workflow_info: WorkflowInfo | None = Field(default=None, description="The information about the agent workflow run")
    visibility: VisibilityOutput | None = Field(
        default=None, description="The visibility information for the agent workflow run"
    )


class CaseInfoExtended(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    data: CaseRawData | None = Field(default=None, description="Raw data of the case, if available")
    docs_analysis: CaseDocsAnalysis | None = Field(default=None, description="Analysis of the documents in the case")
    case_id: str | None = Field(default="", description="Unique identifier for the case", title="Case Id")


class DraftEvaluationsSummaryInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    draft_id: str = Field(..., description="Unique identifier for this draft", title="Draft Id")
    version: str = Field(
        ..., description="Version string extracted from draft_id (e.g., '1.a', '2.b', '3')", title="Version"
    )
    summary: str = Field(..., description="Brief summary of the draft's strategy", title="Summary")
    reasoning: str = Field(..., description="Strategic reasoning behind this draft", title="Reasoning")
    evaluation_count: int = Field(
        ..., description="Total number of evaluations for this draft", title="Evaluation Count"
    )
    latest_grade: float | None = Field(
        default=None,
        description="Most recent overall grade (same as all_evaluations[-1].overall_grade if exists)",
        title="Latest Grade",
    )
    is_selected: bool | None = Field(
        default=False, description="Whether this is the currently selected default draft", title="Is Selected"
    )
    all_evaluations: list[ReplyGradeOutputInput] | None = Field(
        default=None, description="All evaluations for this draft, in chronological order", title="All Evaluations"
    )
    refined_from_draft_id: str | None = Field(
        default=None, description="The ID of the draft this version was refined from.", title="Refined From Draft Id"
    )
    refinement_lineage: list[str] | None = Field(
        default=None,
        description="A complete, ordered list of draft IDs from the origin of this refinement chain to this version.",
        title="Refinement Lineage",
    )


class DraftEvaluationsSummaryOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    draft_id: str = Field(..., description="Unique identifier for this draft", title="Draft Id")
    version: str = Field(
        ..., description="Version string extracted from draft_id (e.g., '1.a', '2.b', '3')", title="Version"
    )
    summary: str = Field(..., description="Brief summary of the draft's strategy", title="Summary")
    reasoning: str = Field(..., description="Strategic reasoning behind this draft", title="Reasoning")
    evaluation_count: int = Field(
        ..., description="Total number of evaluations for this draft", title="Evaluation Count"
    )
    latest_grade: float | None = Field(
        default=None,
        description="Most recent overall grade (same as all_evaluations[-1].overall_grade if exists)",
        title="Latest Grade",
    )
    is_selected: bool | None = Field(
        default=False, description="Whether this is the currently selected default draft", title="Is Selected"
    )
    all_evaluations: list[ReplyGradeOutputOutput] | None = Field(
        default=None, description="All evaluations for this draft, in chronological order", title="All Evaluations"
    )
    refined_from_draft_id: str | None = Field(
        default=None, description="The ID of the draft this version was refined from.", title="Refined From Draft Id"
    )
    refinement_lineage: list[str] | None = Field(
        default=None,
        description="A complete, ordered list of draft IDs from the origin of this refinement chain to this version.",
        title="Refinement Lineage",
    )


class DynamicAgentConfig(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    model: str | None = Field(
        default=None,
        description="Global model override - applies to ALL agents unless overridden in 'agents'",
        title="Model",
    )
    aliases: dict[str, str] | None = Field(
        default=None, description="Alias mappings to merge with existing configuration for this run", title="Aliases"
    )
    agents: dict[str, ModelInfo] | None = Field(
        default=None,
        description="Per-agent model configuration overrides. Keys are agent name_id values.",
        title="Agents",
    )


class EvaluateDraftPayload(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    draft: CreateReplyOutput
    agent_config: DynamicAgentConfig | None = Field(
        default=None,
        description="Dynamic agent configuration as a JSON object. If provided, this will override the workflow's current agent configuration for the evaluation.",
    )


class EvaluationStatusResponse(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    workflow_status: str = Field(
        ..., description="The current status of the workflow execution.", title="Workflow Status"
    )
    original_workflow_id: str | None = Field(
        default=None,
        description="The ID of the parent workflow that initiated this evaluation task.",
        title="Original Workflow Id",
    )
    draft_id: str | None = Field(default=None, description="The ID of the draft being evaluated.", title="Draft Id")
    is_merged: bool = Field(..., description="True if this is a merged evaluation, False otherwise.", title="Is Merged")
    evaluation: ReplyGradeOutputOutput | None = Field(
        default=None, description="The resulting evaluation (either single or merged)."
    )
    original_evaluations: list[ReplyGradeOutputBaseOutput] | None = Field(
        default=None,
        description="For merged evaluations, this contains the list of original evaluations that were merged.",
        title="Original Evaluations",
    )


class PhotoAnalyzerOutput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    rooms: list[RoomAnalysisOutput] | None = Field(
        default=None, description="A list of rooms, each with its grouped photo analyses.", title="Rooms"
    )
    building_exterior: list[RoomAnalysisOutput] | None = Field(
        default=None,
        description="Analyses of photos of the building's exterior or common areas.",
        title="Building Exterior",
    )
    summary: PhotoSummaryOutput | None = Field(default=None, description="An overall summary of the property analysis.")
    pdf_report_full_url: str | None = Field(
        default=None, description="The S3 path to the full, verbose PDF report.", title="Pdf Report Full Url"
    )
    pdf_report_concise_url: str | None = Field(
        default=None,
        description="The S3 path to the concise PDF report (summary, titles, photos only).",
        title="Pdf Report Concise Url",
    )
    pdf_report_minimal_url: str | None = Field(
        default=None,
        description="The S3 path to the minimal PDF report (photos only, grouped by category).",
        title="Pdf Report Minimal Url",
    )


class RelationToolInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    statement_of_claim: Content
    statement_of_defense: Content
    other_documents: list[Content] | None = Field(
        default=None,
        description="List of other documents to compare with the claim and defense",
        title="Other Documents",
    )
    documents_not_provided_by_defendant: list[str] | None = Field(
        default=None,
        description="List of document names mentioned by the defendant but not provided.",
        title="Documents Not Provided By Defendant",
    )
    reply_examples: list[Content] | None = Field(
        default=None, description="List of example replies to the claim and defense", title="Reply Examples"
    )
    reply_snippets: list[ReplySnippet] | None = Field(
        default=None,
        description="List of lawyer-written snippets to use for generating the reply.",
        title="Reply Snippets",
    )
    attributes: dict[str, list[CagentsAgentsRelationtoolModelsRelationToolAttribute]] | None = Field(
        default=None,
        description="Dictionary of attributes with categories as keys and lists of attributes as values",
        title="Attributes",
    )
    topics: list[Topic] | None = Field(
        default=None, description="A list of specific legal topics to look for in the documents.", title="Topics"
    )
    relationtable_feedback: list[FeedbackItem] | None = Field(
        default=None,
        description="List of structured feedback items for the relation table agent",
        title="Relationtable Feedback",
    )
    relationtable_feedbacks: list[str] | None = Field(
        default=None,
        description="List of simple text feedback for the relation table agent",
        title="Relationtable Feedbacks",
    )
    feedbacks: list[FeedbackItem] | None = Field(
        default=None, description="List of structured feedback items for the draft reply", title="Feedbacks"
    )
    initial_draft: Content | None = Field(
        default=None,
        description="Optional initial draft to refine from the start. If provided, the workflow will evaluate and refine this draft instead of generating from scratch.",
    )
    to_language: str | None = Field(
        default="de",
        description="The language to translate the summary to. E.g., 'en' for English, 'de' for German.",
        title="To Language",
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Metadata for the relation tool input", title="Metadata"
    )
    case_info: CaseInfoExtended | None = Field(default=None, description="Information about the case, if available")
    only_disagreement: bool | None = Field(
        default=False, description="List only disagreement, if false, list all attributes", title="Only Disagreement"
    )
    include_case_docs: bool | None = Field(
        default=True, description="Include case documents from Conny in the context", title="Include Case Docs"
    )
    run_document_analysis: bool | None = Field(
        default=False, description="Whether to run the document analysis step", title="Run Document Analysis"
    )
    run_legal_analysis: bool | None = Field(
        default=False, description="Whether to run the legal argument analysis step", title="Run Legal Analysis"
    )
    run_create_reply: bool | None = Field(
        default=False, description="Whether to run the create reply step", title="Run Create Reply"
    )
    run_draft_evaluation: bool | None = Field(
        default=True,
        description="Whether to run the draft evaluation step after creating a reply",
        title="Run Draft Evaluation",
    )
    run_timeout_days: int | None = Field(
        default=3,
        description="How long the interactive workflow should wait for updates, in days.",
        title="Run Timeout Days",
    )
    use_reply_examples: bool | None = Field(
        default=True, description="Whether to use reply examples for the first draft.", title="Use Reply Examples"
    )


class WorkflowEvaluationsResponse(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    workflow_id: str = Field(..., description="The main workflow ID", title="Workflow Id")
    total_drafts: int = Field(..., description="Total number of drafts generated", title="Total Drafts")
    total_evaluations: int = Field(
        ..., description="Total number of evaluations across all drafts", title="Total Evaluations"
    )
    selected_draft_id: str | None = Field(
        default=None, description="The currently selected default draft ID, if any", title="Selected Draft Id"
    )
    auto_selected_draft_id: str | None = Field(
        default=None,
        description="The draft ID with the best evaluation from the latest version, selected automatically.",
        title="Auto Selected Draft Id",
    )
    draft_ids_ordered: list[str] | None = Field(
        default=None, description="List of draft IDs in version order (v1, v2, v3, ...)", title="Draft Ids Ordered"
    )
    drafts: dict[str, DraftEvaluationsSummaryOutput] | None = Field(
        default=None, description="Dictionary of drafts keyed by draft_id for O(1) lookup", title="Drafts"
    )


class WorkflowInputTextSummarizerWorkflowContext(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    agent_input: AgentInputTextSummarizerWorkflowContext = Field(
        ..., description="The agent's input data (context and llm_input)"
    )
    agent_config: DynamicAgentConfig | None = Field(
        default=None, description="Optional runtime configuration for agents (models, aliases)"
    )
    wid: WorkflowInfo | None = Field(default=None, description="The ID and metadata of the temporal workflow")
    visibility: VisibilityInput | None = Field(
        default=None, description="The visibility information for the agent workflow run"
    )


class AddFeedbackPayload(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    grade: ReplyGradeOutputInput | None = Field(default=None, description="A full grade object for feedback.")
    feedbacks: list[FeedbackItem] | None = Field(
        default=None, description="A list of simple feedback items.", title="Feedbacks"
    )
    agent_config: DynamicAgentConfig | None = Field(
        default=None,
        description="Dynamic agent configuration as a JSON object. If provided, this will override the workflow's current agent configuration for the new iteration.",
    )


class AgentCaseSummaryWorkflowInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    agent_input: AgentInputConnyRequestSummaryCtx = Field(
        ..., description="The agent's input data (context and llm_input)"
    )
    agent_config: DynamicAgentConfig | None = Field(
        default=None, description="Optional runtime configuration for agents (models, aliases)"
    )
    wid: WorkflowInfo | None = Field(default=None, description="The ID and metadata of the temporal workflow")
    visibility: VisibilityInput | None = Field(
        default=None, description="The visibility information for the agent workflow run"
    )


class AgentClassifierWorkflowInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    agent_input: AgentInputClassificationRentalCtx = Field(
        ..., description="The agent's input data (context and llm_input)"
    )
    agent_config: DynamicAgentConfig | None = Field(
        default=None, description="Optional runtime configuration for agents (models, aliases)"
    )
    wid: WorkflowInfo | None = Field(default=None, description="The ID and metadata of the temporal workflow")
    visibility: VisibilityInput | None = Field(
        default=None, description="The visibility information for the agent workflow run"
    )


class AgentInputRelationToolInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    context: RelationToolInput = Field(..., description="The input data for the agent")
    llm_input: str | None = Field(default="", description="The LLM input string for the agent", title="Llm Input")


class AgentPhotoAnalyzerWorkflowInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    agent_input: AgentInputPhotoAnalyzerWorkflowInput = Field(
        ..., description="The agent's input data (context and llm_input)"
    )
    agent_config: DynamicAgentConfig | None = Field(
        default=None, description="Optional runtime configuration for agents (models, aliases)"
    )
    wid: WorkflowInfo | None = Field(default=None, description="The ID and metadata of the temporal workflow")
    visibility: VisibilityInput | None = Field(
        default=None, description="The visibility information for the agent workflow run"
    )


class AgentRelationToolEvaluateQualityWorkflowInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    agent_input: AgentInputRelationToolEvaluateQualityInput = Field(
        ..., description="The agent's input data (context and llm_input)"
    )
    agent_config: DynamicAgentConfig | None = Field(
        default=None, description="Optional runtime configuration for agents (models, aliases)"
    )
    wid: WorkflowInfo | None = Field(default=None, description="The ID and metadata of the temporal workflow")
    visibility: VisibilityInput | None = Field(
        default=None, description="The visibility information for the agent workflow run"
    )


class AgentRelationToolWorkflowInput(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )
    agent_input: AgentInputRelationToolInput = Field(..., description="The agent's input data (context and llm_input)")
    agent_config: DynamicAgentConfig | None = Field(
        default=None, description="Optional runtime configuration for agents (models, aliases)"
    )
    wid: WorkflowInfo | None = Field(default=None, description="The ID and metadata of the temporal workflow")
    visibility: VisibilityInput | None = Field(
        default=None, description="The visibility information for the agent workflow run"
    )


WorkflowStepInput.model_rebuild()
WorkflowStepOutput.model_rebuild()
