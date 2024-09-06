import React, { Fragment } from 'react';
import { Col } from 'reactstrap';
import { H5 } from '../../AbstractElements';
import { FeaturedTutorials } from '../../Constant';
import FeaturesTutorial from '../Knowledgebase/KnowledgeBase/FeaturesTutorial';

const FAQFeaturesTutorial = () => {
    return (
        <Fragment>
            <Col lg="12" className="featured-tutorial">
                <div className="header-faq">
                    <H5 className="mb-0">{FeaturedTutorials}</H5>
                </div>
                <FeaturesTutorial />
            </Col>
        </Fragment>
    );
};
export default FAQFeaturesTutorial;