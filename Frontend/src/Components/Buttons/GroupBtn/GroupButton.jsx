import React, { Fragment } from 'react';
import { Row, Col, Card, CardBody, ButtonGroup } from 'reactstrap';
import { Btn } from '../../../AbstractElements';
import HeaderCard from '../../Common/Component/HeaderCard';
import { GroupBtnData } from '../../Common/Data/Buttons';

const GroupButtonClass = () => {
    return (
        <Fragment>
            {GroupBtnData.map((item, i) =>
                <div className="col-12" key={i}>
                    <Card>
                        <HeaderCard title={item.title} />
                        <CardBody>
                            <div className="btn-group-showcase">
                                <Row>
                                    {item.color.map((colorItem, i) =>
                                        <Col xl="4" md="6" sm="12" className={`xl-50 ${colorItem.colClass ? colorItem.colClass : ''}`} key={i}>
                                            <ButtonGroup className={colorItem.btnClass ? colorItem.btnClass : ''}>
                                                <Btn attrBtn={{ size: colorItem.size ? colorItem.size : '', color: colorItem.colorClass, outline: colorItem.outline1 ? true : false }} >{colorItem.title1}</Btn>
                                                <Btn attrBtn={{ size: colorItem.size ? colorItem.size : '', color: colorItem.colorClass, outline: colorItem.outline2 ? true : false }} >{colorItem.title2}</Btn>
                                                <Btn attrBtn={{ size: colorItem.size ? colorItem.size : '', color: colorItem.colorClass, outline: colorItem.outline3 ? true : false }} >{colorItem.title3}</Btn>
                                            </ButtonGroup>
                                        </Col>
                                    )}
                                </Row>
                            </div>
                        </CardBody>
                    </Card>
                </div>
            )}

        </Fragment>
    );
};

export default GroupButtonClass;