import { H5, Btn } from '../../../../AbstractElements';
import React, { Fragment, useState } from 'react';
import { Card, CardBody, CardHeader, Col, Collapse, Input, Label } from 'reactstrap';

const JobTitleClass = () => {
    const [isFilter, setIsFilter] = useState(true);
    return (
        <Fragment>
            <Col xl="12">
                <Card>
                    <CardHeader>
                        <H5 className="mb-0 p-0">
                            <Btn attrBtn={{ className: 'btn btn-link', onClick: () => setIsFilter(!isFilter), color: 'transperant' }} >Job Title</Btn>
                        </H5>
                    </CardHeader>
                    <Collapse isOpen={isFilter}>
                        <CardBody className="animate-chk">
                            <Label className="d-block" for="chk-ani11">
                                <Input className="checkbox_animated" id="chk-ani11" type="checkbox" />UI/Ux designer(25)
                            </Label>
                            <Label className="d-block" for="chk-ani12">
                                <Input className="checkbox_animated" id="chk-ani12" type="checkbox" /> Graphic designer(10)
                            </Label>
                            <Label className="d-block" for="chk-ani13">
                                <Input className="checkbox_animated" id="chk-ani13" type="checkbox" /> Front end designer(15)
                            </Label>
                            <Label className="d-block" for="chk-ani14">
                                <Input className="checkbox_animated" id="chk-ani14" type="checkbox" /> PHP developer(42)
                            </Label>
                            <Label className="d-block mb-0" for="chk-ani15">
                                <Input className="checkbox_animated" id="chk-ani15" type="checkbox" />React Developer(5)
                            </Label>
                        </CardBody>
                        <Btn attrBtn={{ className: 'btn d-block w-100 text-center', color: 'primary', type: 'button' }} >All Job Title</Btn>
                    </Collapse>
                </Card>
            </Col>
        </Fragment>
    );
};

export default JobTitleClass;