"""
sphn_schema_graph.py: 
    Part of the example dicom2sphn package.
    It contains the SPHNSchemaGraph class, which represents the SPHN rdf schema graph and provides methods to interact with it.
"""
from pathlib import Path
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import NamespaceManager, OWL, RDF

from .tools import is_valid_string, make_clean


# Other Namespaces
SPHN     = Namespace("https://biomedit.ch/rdf/sphn-schema/sphn#")
SPHN_IND = Namespace("https://biomedit.ch/rdf/sphn-schema/sphn/individual#")
SPHN_DCM = Namespace("https://biomedit.ch/rdf/sphn-resource/dcm/")

UCUM     = Namespace("https://biomedit.ch/rdf/sphn-resource/ucum/")
EDAM     = Namespace("http://edamontology.org/")
SNOMED   = Namespace("http://snomed.info/id/")

# RESOURCE = Namespace("https://biomedit.ch/rdf/sphn-resource/")

# Future project?
#DMIB     = Namespace("https://biomedit.ch/rdf/sphn-schema/dmib#")
#DMIB_IND = Namespace("https://biomedit.ch/rdf/sphn-schema/dmib/individual#")

#
# The SPHN Schema Graph class representing the SPHN RDF schema graph and providing methods to interact with it.
#
class SPHNSchemaGraph:
    
    _file_path: Path
    _graph: Graph
    _version_iri: URIRef

    def __init__(self, sphn_rdf_schema_file_path: Path):
        """ 
        Initializes the instance
        """
        # Checks
        assert isinstance(sphn_rdf_schema_file_path, Path)
        assert sphn_rdf_schema_file_path.is_file()

        # Read the SPHN RDF schema file into a graph
        graph = Graph()
        graph.parse(sphn_rdf_schema_file_path)

        if len(graph) == 0:
            raise ValueError(f"SPHN RDF schema graph is empty after reading the file '{sphn_rdf_schema_file_path}'. Please check the file path and content.")

        # Save the graph and file path
        self._graph = graph 
        self._file_path = sphn_rdf_schema_file_path

        # Query for version
        version_iri = self.query_for_version()

        if version_iri is None: 
            raise ValueError(f"SPHN RDF Schema version could not be found in the file '{sphn_rdf_schema_file_path}'. Please check the file path and content.")

        if not isinstance(version_iri, URIRef): 
            raise ValueError("SPHN RDF Schema version has an invalid type.")

        # Save the version IRI
        self._version_iri = version_iri


    # -----------------------------------------------------------------------------------------------------------------
    # Public functions
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-07-06
    #
    def namespace_manager(self) -> NamespaceManager|None:
        """ 
        Gives the NamespaceManager
        """
        return self._graph.namespace_manager if self._graph is not None else None

    #
    # Edwin 2026-07-06
    #
    def get_version(self) -> URIRef:
        """ 
        Returns the SPHN schema version as a URIRef
        """
        
        return self._version_iri

    #
    # Edwin 2026-07-09
    #
    def is_sphn_data_provider_category_value_set_member(self, category: str) -> bool:
        """ 
        Checks if category is a valid sphn:DataProvider_category value set member
        """
        # Checks
        assert is_valid_string(category)
        assert category == make_clean(category)

        # Create the triple
        subj_01 = URIRef(SPHN_IND+category)
        pred_01 = RDF.type
        obj_01 = SPHN.DataProvider_category
        
        return True if (subj_01, pred_01, obj_01) in self._graph else False

    #
    # Edwin 2026-07-09
    #
    def is_sphn_source_system_purpose_value_set_member(self, purpose: str) -> bool:
        """ 
        Checks if purpose is a valid sphn:SourceSystem_purpose value set member
        """
        # Checks
        assert is_valid_string(purpose)
        assert purpose == make_clean(purpose)

        # Create the triple
        subj_01 = URIRef(SPHN_IND+purpose)
        pred_01 = RDF.type
        obj_01 = SPHN.SourceSystem_purpose
        
        return True if (subj_01, pred_01, obj_01) in self._graph else False

    #
    # Edwin 2026-07-09
    #
    def is_sphn_source_system_category_value_set_member(self, category: str) -> bool:
        """ 
        Checks if category is a valid sphn:SourceSystem_category value set member
        """
        # Checks
        assert is_valid_string(category)
        assert category == make_clean(category)

        # Create the triple
        subj_01 = URIRef(SPHN_IND+category)
        pred_01 = RDF.type
        obj_01 = SPHN.SourceSystem_category
        
        return True if (subj_01, pred_01, obj_01) in self._graph else False

    #
    # Edwin 2026-07-09
    #
    def is_sphn_comparator_value_set_member(self, comparator: str) -> bool:
        """ 
        Checks if comparator is a valid sphn:Comparator value set member
        """
        # Checks
        assert is_valid_string(comparator)
        assert comparator == make_clean(comparator)

        # Create the triple
        subj_01 = URIRef(SPHN_IND+comparator)
        pred_01 = RDF.type
        obj_01 = SPHN.Comparator
        
        return True if (subj_01, pred_01, obj_01) in self._graph else False

    #
    # Edwin 2026-07-09
    #
    def is_sphn_hash_algorithm_value_set_member(self, algorithm: str) -> bool:
        """ 
        Checks if algorithm is a valid sphn:Hash_algorithm value set member
        """
        # Checks
        assert is_valid_string(algorithm)
        assert algorithm == make_clean(algorithm)

        # Create the triple
        subj_01 = URIRef(SPHN_IND+algorithm)
        pred_01 = RDF.type
        obj_01 = SPHN.Hash_algorithm
        
        return True if (subj_01, pred_01, obj_01) in self._graph else False

    #
    # Edwin 2026-07-09
    #
    def is_sphn_data_compression_algorithm_type_value_set_member(self, type: str) -> bool:
        """ 
        Checks if type is a valid sphn:DataCompressionAlgorithm_type value set member
        """
        # Checks
        assert is_valid_string(type)
        assert type == make_clean(type)

        # Create the triple
        subj_01 = URIRef(SPHN_IND+type)
        pred_01 = RDF.type
        obj_01 = SPHN.DataCompressionAlgorithm_type
        
        return True if (subj_01, pred_01, obj_01) in self._graph else False

    #
    # Edwin 2026-07-09
    #
    def is_sphn_data_compression_algorithm_method_value_set_member(self, method: str) -> bool:
        """ 
        Checks if method is a valid sphn:DataCompressionAlgorithm_method value set member
        """
        # Checks
        assert is_valid_string(method)
        assert method == make_clean(method)

        # Create the triple
        subj_01 = URIRef(SPHN_IND+method)
        pred_01 = RDF.type
        obj_01 = SPHN.DataCompressionAlgorithm_method
        
        return True if (subj_01, pred_01, obj_01) in self._graph else False

    #
    # Edwin 2026-07-09
    #
    def is_sphn_data_file_encoding_value_set_member(self, encoding: str) -> bool:
        """ 
        Checks if encoding is a valid sphn:DataFile_encoding value set member
        """
        # Checks
        assert is_valid_string(encoding)
        assert encoding == make_clean(encoding)

        # Create the triple
        subj_01 = URIRef(SPHN_IND+encoding)
        pred_01 = RDF.type
        obj_01 = SPHN.DataFile_encoding
        
        return True if (subj_01, pred_01, obj_01) in self._graph else False

    #
    # Edwin 2026-07-09
    #
    def is_sphn_imaging_frame_content_qualification_value_set_member(self, content_qualification: str) -> bool:
        """ 
        Checks if content_qualification is a valid sphn:ImagingFrame_contentQualification value set member
        """
        # Checks
        assert is_valid_string(content_qualification)
        assert content_qualification == make_clean(content_qualification)

        # Create the triple
        subj_01 = URIRef(SPHN_IND+content_qualification)
        pred_01 = RDF.type
        obj_01 = SPHN.ImagingFrame_contentQualification
        
        return True if (subj_01, pred_01, obj_01) in self._graph else False

    #
    # Edwin 2026-07-09
    #
    def is_sphn_imaging_frame_type_value_set_member(self, image_type: str) -> bool:
        """ 
        Checks if image_type is a valid sphn:ImagingFrame_type value set member
        """
        # Checks
        assert is_valid_string(image_type)
        assert image_type == make_clean(image_type)

        # Create the triple
        subj_01 = URIRef(SPHN_IND+image_type)
        pred_01 = RDF.type
        obj_01 = SPHN.ImagingFrame_type

        return True if (subj_01, pred_01, obj_01) in self._graph else False

    # -----------------------------------------------------------------------------------------------------------------
    # Private functions
    # -----------------------------------------------------------------------------------------------------------------

    #
    # Edwin 2026-07-07
    #
    def query_for_version(self) -> URIRef|None:
        """ 
        Returns the SPHN schema version as a URIRef
        """

        # There should only be one 'versionIRI' for SPHN, so we can use the 'value' function
        #   with 'any=false' raising an UniquenessError Exception in case more then one match was found
        #   with 'default=None' returning None in case no match was found
        # Note: the 'subject' uses '.../sphn' without a '#' at the end, because the 'versionIRI' is a property of the 'sphn' ontology itself, not of the 'sphn#' namespace
        version = self._graph.value(
            subject=URIRef("https://biomedit.ch/rdf/sphn-schema/sphn"), 
            predicate=OWL.versionIRI,
            object=None,
            default=None,
            any=False)
    
        # The returned value can be Node or None. The Node should be of type URIRef.
        assert version is None or isinstance(version, URIRef)

        return version
    
        # Alternative:

        ## Namespaces (prefix's) should already be in the ontology graph
        #sparql_query = """
        #    SELECT ?version
        #        WHERE {
        #            <https://biomedit.ch/rdf/sphn-schema/sphn> owl:versionIRI ?version .
        #        }
        #"""

        ## Run the Query
        #query_result = self.schema_graph.query(sparql_query)
        ## Should give one result
        #if len(query_result) != 1:
        #    # Error
        #    raise ValueError(f"Incorrect number of query results. Expected: '1', received: '{len(query_result)}'")
        #for row in query_result:
        #    return row["version"]