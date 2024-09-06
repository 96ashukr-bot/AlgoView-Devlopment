import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../AbstractElements';
import StarRatingClass from './StarRating';
import HeartRatingClass from './HeartRating';
import ThumbsUpDownRatingClass from './ThumbsUpDownRating';
import PillRatingClass from './PillRating';

const RatingClass = () => {

    return (
        <Fragment>
            <Breadcrumbs mainTitle="Rating" parent="Bonus Ui" title="Rating" />
            <Container fluid={true}>
                <Row>
                    <StarRatingClass />
                    <HeartRatingClass />
                    <ThumbsUpDownRatingClass />
                    <PillRatingClass />
                </Row>
            </Container>
        </Fragment >
    );
};

export default RatingClass;