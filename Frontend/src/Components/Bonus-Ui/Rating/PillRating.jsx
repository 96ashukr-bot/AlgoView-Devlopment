import React, { Fragment } from 'react';
import { Col, Card, CardBody } from 'reactstrap';
import Rating from 'react-rating';
import HeaderCard from '../../Common/Component/HeaderCard';
import { PillRating } from '../../../Constant';

const PillRatingClass = () => {
    return (
        <Fragment>
            <Col xl="6" lg="12" md="6">
                <Card>
                    <HeaderCard title={PillRating} />
                    <CardBody>
                        <Rating
                            className="rating"
                            emptySymbol={<span style={{ margin: '10px' }}>---</span>}
                            fullSymbol={['A', 'B', 'C', 'D', 'E'].map(n => <span style={{ fontSize: '20px' }}>{n}</span>)}
                            onClick={(rate) => alert(rate)}
                        >
                        </Rating>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default PillRatingClass;