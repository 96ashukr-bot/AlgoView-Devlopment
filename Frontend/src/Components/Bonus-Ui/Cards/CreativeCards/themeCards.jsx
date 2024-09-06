import React, { Fragment } from 'react';
import { Col, Card, CardHeader, CardBody } from 'reactstrap';
import { H5, P } from '../../../../AbstractElements';
import { CreativeCardData } from '../../../Common/Data/Bonus-ui';

const CreativeCardsCommon = () => {
    return (
        <Fragment>
            {CreativeCardData.map((item) =>
                <Col sm="12" xl="6" key={item.id}>
                    <Card className={item.cardClass ? item.cardClass : ''}>
                        <CardHeader className={item.headerClass}>
                            <H5>{item.title}</H5>
                        </CardHeader>
                        <CardBody>
                            <P>
                                {item.pare}
                            </P>
                        </CardBody>
                    </Card>
                </Col>
            )}
        </Fragment>
    );
};

export default CreativeCardsCommon;