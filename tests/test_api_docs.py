from drf_spectacular.generators import SchemaGenerator


def test_field_schema():
    schema = SchemaGenerator().get_schema(request=None, public=True)

    zaaktype_schema = schema["components"]["schemas"]["Zaak"]["properties"]["zaaktype"]
    assert zaaktype_schema == {
        "type": "string",
        "format": "uri",
        "maxLength": 1000,
        "minLength": None,
    }


def test_filter_schema():
    schema = SchemaGenerator().get_schema(request=None, public=True)

    parameters_schema = schema["paths"]["/zaken/"]["get"]["parameters"]

    assert len(parameters_schema) == 2

    zaaktype_param = parameters_schema[0]
    assert zaaktype_param["name"] == "zaaktype"
    assert zaaktype_param["schema"]["type"] == "string"
    assert zaaktype_param["schema"]["format"] == "uri"

    zaaktype_in_param = parameters_schema[1]
    assert zaaktype_in_param["name"] == "zaaktype__in"
    assert zaaktype_in_param["schema"]["type"] == "array"
    assert zaaktype_in_param["schema"]["items"]["type"] == "string"
    assert zaaktype_in_param["schema"]["items"]["format"] == "uri"


def test_declared_filter_schema():
    schema = SchemaGenerator().get_schema(request=None, public=True)

    parameters_schema = schema["paths"]["/zaakobjectfk/"]["get"]["parameters"]

    assert len(parameters_schema) == 1
    param = parameters_schema[0]

    assert param["name"] == "zaak"
    assert param["schema"]["type"] == "string"
    assert param["schema"]["format"] == "uri"
