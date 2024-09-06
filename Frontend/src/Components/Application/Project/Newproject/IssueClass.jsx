import React, { Fragment } from 'react';
import { Col, FormGroup, Input, Label, Row } from 'reactstrap';
import { Big, Comment, Issues, Medium, Resolved, Small } from '../../../../Constant';

const IssueClass = ({ register }) => {
    return (
        <Fragment>
            <Row>
                <Col sm="4">
                    <FormGroup>
                        <Label>{Issues}</Label>
                        <Input type="select" name="issues" placeholder="Select Issues" className="form-control digits" required>
                            <option>{Small}</option>
                            <option>{Medium}</option>
                            <option>{Big}</option>
                        </Input>
                    </FormGroup>
                </Col>
                <Col sm="4">
                    <FormGroup>
                        <Label>{Resolved}</Label>
                        <input className="form-control" type="text" name="resolved" placeholder="Add Resolved issues" {...register('resolved',{ required: true })} />
                    </FormGroup>
                </Col>
                <Col sm="4">
                    <FormGroup>
                        <Label>{Comment}</Label>
                        <input className="form-control" type="text" name="comment" placeholder="Add Comment" {...register('comment',{ required: true })} />
                    </FormGroup>
                </Col>
            </Row>
        </Fragment>
    );
};

export default IssueClass;