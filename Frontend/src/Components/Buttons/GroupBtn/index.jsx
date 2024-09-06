import React, { Fragment } from 'react';
import { Container, Row, Col, Card, CardBody, ButtonGroup, UncontrolledDropdown, DropdownToggle, DropdownMenu, DropdownItem } from 'reactstrap';
import { Nesting, Vertical } from '../../../Constant';
import { Breadcrumbs, Btn } from '../../../AbstractElements';
import GroupButtonClass from './GroupButton';
import RadioBtnClass from './RadioBtn';
import HeaderCard from '../../Common/Component/HeaderCard';

const GroupButton = () => {
    return (
        <Fragment>
            <Breadcrumbs mainTitle='Button Group' parent="Buttons" title="Button Group" />
            <Container fluid={true}>
                <Row>
                    <GroupButtonClass />
                    <RadioBtnClass />
                    <Col lg="6">
                        <Card className="height-equal">
                            <HeaderCard title={Nesting} span1="Make nesting buttons" />
                            <CardBody className="btn-group-wrapper">
                                <div className="m-b-30">
                                    <ButtonGroup>
                                        <Btn attrBtn={{ color: 'primary' }} ><i className="fa fa-bold"></i></Btn>
                                        <Btn attrBtn={{ color: 'secondary' }}><i className="fa fa fa-italic"></i></Btn>
                                        <UncontrolledDropdown>
                                            <DropdownToggle color='light'>
                                                {'Dropdown'}
                                            </DropdownToggle>
                                            <DropdownMenu>
                                                <DropdownItem header>{'Header'}</DropdownItem>
                                                <DropdownItem disabled>{'Action'}</DropdownItem>
                                                <DropdownItem>{'Another Action'}</DropdownItem>
                                                <DropdownItem divider />
                                                <DropdownItem>{'Another Action'}</DropdownItem>
                                            </DropdownMenu>
                                        </UncontrolledDropdown>
                                    </ButtonGroup>
                                </div>
                                <div className="m-b-30">
                                    <ButtonGroup>
                                        <Btn attrBtn={{ color: 'primary' }} ><i className="fa fa-bold"></i></Btn>
                                        <Btn attrBtn={{ color: 'secondary' }} ><i className="fa fa fa-italic"></i></Btn>
                                        <Btn attrBtn={{ color: 'success' }} ><i className="fa fa-file-image-o"></i></Btn>
                                        <Btn attrBtn={{ color: 'info' }} ><i className="fa fa-paperclip"></i></Btn>
                                    </ButtonGroup>
                                </div>
                                <div className="m-b-30">
                                    <ButtonGroup>
                                        <Btn attrBtn={{ color: 'primary', size: 'lg' }}  ><i className="fa fa-bold"></i></Btn>
                                        <Btn attrBtn={{ color: 'secondary', size: 'lg' }} ><i className="fa fa fa-italic"></i></Btn>
                                        <Btn attrBtn={{ color: 'success', size: 'lg' }} ><i className="fa fa-file-image-o"></i></Btn>
                                        <Btn attrBtn={{ color: 'info', size: 'lg' }} ><i className="fa fa-paperclip"></i></Btn>
                                    </ButtonGroup>
                                </div>
                            </CardBody>
                        </Card>
                    </Col>
                    <Col lg="6">
                        <Card className="height-equal">
                            <HeaderCard title={Vertical} span1="Make vertical buttons" />
                            <CardBody className="btn-group-wrapper">
                                <ButtonGroup vertical >
                                    <Btn attrBtn={{ color: 'primary', type: 'button' }} >{'Button'}</Btn>
                                    <Btn attrBtn={{ color: 'secondary', type: 'button', className: 'b-r-0' }}>{'Button'}</Btn>
                                    <UncontrolledDropdown>
                                        <DropdownToggle color='success' caret className="b-r-0">
                                            {'Button Dropdown'}
                                        </DropdownToggle>
                                        <DropdownMenu>
                                            <DropdownItem>{'Another Action'}</DropdownItem>
                                            <DropdownItem>{'Another Action'}</DropdownItem>
                                        </DropdownMenu>
                                    </UncontrolledDropdown>
                                    <Btn attrBtn={{ color: 'info', type: 'button', className: 'b-r-0' }} >{'Button'}</Btn>
                                    <Btn attrBtn={{ color: 'warning', type: 'button', className: 'b-r-0' }} >{'Button'}</Btn>
                                    <UncontrolledDropdown>
                                        <DropdownToggle color='danger' caret>
                                            {'Button Dropdown'}
                                        </DropdownToggle>
                                        <DropdownMenu>
                                            <DropdownItem>{'Another Action'}</DropdownItem>
                                            <DropdownItem>{'Another Action'}</DropdownItem>
                                        </DropdownMenu>
                                    </UncontrolledDropdown>
                                </ButtonGroup>
                            </CardBody>
                        </Card>
                    </Col>
                </Row>
            </Container>
        </Fragment>
    );
};

export default GroupButton;