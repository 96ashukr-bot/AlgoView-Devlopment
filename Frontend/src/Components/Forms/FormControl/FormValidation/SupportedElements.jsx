import React, { Fragment } from "react";
import { Card, CardBody, Form, FormGroup, Label, Input } from 'reactstrap'
import { SupportedElements } from "../../../../Constant";
import HeaderCard from "../../../Common/Component/HeaderCard";

const SupportedElementsClass = () => {
    return (
        <Fragment>
            <Card>
                <HeaderCard title={SupportedElements} span1="Not interested in custom validation feedback messages or writing JavaScript to change form behaviors? All good, you can use the browser defaults. Try submitting the form below. Depending on your browser and OS, you’ll see a slightly different style of feedback." span2="While these feedback styles cannot be styled with CSS, you can still customize the feedback text through JavaScript." />
                <CardBody>
                    <Form className="was-validated">
                        <div className="custom-control custom-checkbox form-check mb-3">
                            <Input className="custom-control-input" id="customControlValidation1" type="checkbox" required />
                            <Label className="custom-control-label" htmlFor="customControlValidation1">{"Check this custom checkbox"}</Label>
                            <div className="invalid-feedback">{"Example invalid feedback text"}</div>
                        </div>
                        <div className="custom-control form-check custom-radio">
                            <Input className="custom-control-input" id="customControlValidation2" type="radio" name="radio-stacked" required />
                            <Label className="custom-control-label" htmlFor="customControlValidation2">{"Toggle this custom radio"}</Label>
                        </div>
                        <div className="custom-control form-check custom-radio mb-3">
                            <Input className="custom-control-input" id="customControlValidation3" type="radio" name="radio-stacked" required />
                            <Label className="custom-control-label" htmlFor="customControlValidation3">{"Or toggle this other custom radio"}</Label>
                            <div className="invalid-feedback">{"More example invalid feedback text"}</div>
                        </div>
                        <FormGroup>
                            <Input type="select" className="form-select" required="">
                                <option value="">{"Open this select menu"}</option>
                                <option value="1">{"One"}</option>
                                <option value="2">{"Two"}</option>
                                <option value="3">{"Three"}</option>
                            </Input>
                            <div className="invalid-feedback">{"Example invalid custom select feedback"}</div>
                        </FormGroup>
                        <div className="custom-file">
                            <Input className="custom-file-input" id="validatedCustomFile" type="file" required="" />
                            <div className="invalid-feedback">{"Example invalid custom file feedback"}</div>
                        </div>
                    </Form>
                </CardBody>
            </Card>
        </Fragment>
    )
}

export default SupportedElementsClass;