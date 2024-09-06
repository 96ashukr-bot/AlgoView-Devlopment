import { H6 } from '../../../../AbstractElements';
import { UploadCoverLetter, UploadRecommendations, UploadYourCV, UploadYourFiles } from '../../../../Constant';
import React, { Fragment } from 'react';
import { Col, Form, FormGroup, Input, Label, Row } from 'reactstrap';

const UploadFileClass = () => {
    return (
        <Fragment>
            <H6 className="mb-0">{UploadYourFiles}</H6>
            <Form className="theme-form">
                <Row>
                    <Col>
                        <FormGroup>
                            <Label className="col-form-label pt-0">{UploadCoverLetter}:<span className="font-danger">*</span></Label>
                            <Input className="form-control" type="file" />
                        </FormGroup>
                    </Col>
                </Row>
                <Row>
                    <Col>
                        <FormGroup>
                            <Label className="col-form-label pt-0">{UploadYourCV}:<span className="font-danger">*</span></Label>
                            <Input className="form-control" type="file" />
                        </FormGroup>
                    </Col>
                </Row>
                <Row>
                    <Col>
                        <div>
                            <Label className="col-form-label pt-0">{UploadRecommendations}:</Label>
                            <Input className="form-control" type="file" />
                        </div>
                    </Col>
                </Row>
            </Form>
        </Fragment>
    );
};

export default UploadFileClass;