import React, { Fragment } from 'react';
import { Col, Card, CardBody } from 'reactstrap';
import { P, Ribbon } from '../../../AbstractElements';
import { RibbonData } from '../../Common/Data/Bonus-ui';

const RibbonComponent = () => {
    return (
        <Fragment>
            {RibbonData.map((item) =>
                <Col key={item.id} md='12' lg='6' xl='4'>
                    <Card className={item.wrapperClass}>
                        <CardBody>
                            <Ribbon attrRibbons={{ className: item.class }} >{item.title}</Ribbon>
                            <P>{item.pera}</P>
                        </CardBody>
                    </Card>
                </Col>
            )}
        </Fragment>
    );
};

export default RibbonComponent;