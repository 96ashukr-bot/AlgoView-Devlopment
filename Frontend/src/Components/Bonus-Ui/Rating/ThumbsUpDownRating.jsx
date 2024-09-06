import React, { Fragment, useState } from "react";
import { Row, Col, Card, CardBody } from 'reactstrap'
import Rating from 'react-rating';
import HeaderCard from "../../Common/Component/HeaderCard";
import { H6 } from "../../../AbstractElements";
import { ThumbsUpDownRating } from "../../../Constant";

const ThumbsUpDownRatingClass = () => {
    const [thumbs, setThumbs] = useState(0)
    return (
        <Fragment>
            <Col xl="6" lg="12" md="6">
                <Card>
                    <HeaderCard title={ThumbsUpDownRating} />
                    <CardBody>
                        <Row className="rating">
                            <Col sm="8">
                                <Rating
                                    initialRating={thumbs}
                                    emptySymbol="fa fa-thumbs-down fa-2x"
                                    fullSymbol="fa fa-thumbs-up fa-2x"
                                    onHover={(rate) => setThumbs(rate)}
                                >
                                </Rating>
                            </Col>
                            <Col sm="4">
                                <H6 attrH6={{ className: "mb-0 text-end" }} >{"You Rated"} : {thumbs}</H6>
                            </Col>
                        </Row>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    )
}

export default ThumbsUpDownRatingClass;