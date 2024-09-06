import React, { Fragment } from 'react';
import { BasicCardData } from '../../../Common/Data/Bonus-ui';
import { Col, Card, CardHeader, CardBody, CardFooter } from 'reactstrap';
import { H5, H6, P } from '../../../../AbstractElements';

const BasicCommon = () => {
    return (
        <Fragment>
            {BasicCardData.map((item) =>
                <Col sm="12" xl="6" key={item.id}>
                    <Card>
                        <CardHeader className={item.colorClass ? item.colorClass : item.headerClass ? item.headerClass : ''}>
                            <H5>{item.icon ? item.icon : ''}{item.title}</H5>
                            {item.span ? <span>{item.span}</span> : ''}
                        </CardHeader>
                        <CardBody className={item.colorClass ? item.colorClass : item.bodyClass ? item.bodyClass : ''}>
                            <P attrPara={{ className: 'mb-0' }}>
                                {item.pare}
                            </P>
                        </CardBody>
                        {item.footer ?
                            <CardFooter className={item.colorClass ? item.colorClass : item.footerClass ? item.footerClass : ''}>
                                <H6 attrH6={{ className: 'mb-0' }}>{item.footer}</H6>
                            </CardFooter>
                            : ''}
                    </Card>
                </Col>
            )}

        </Fragment>

    );
};

export default BasicCommon;