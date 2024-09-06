import { Breadcrumbs, H5 } from '../../../AbstractElements';
import Articals from './Articals';
import FeaturesTutorial from './FeaturesTutorial';
import HeaderPart from './HeaderPart';
import { Col, Container, Row } from 'reactstrap';
import React, { Fragment } from 'react';
import BrowseArticlesClass from './BrowseArticles';
import LatestArticlesClass from './LatestArticlesClass';

const KnowledgeBaseContain = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Knowledgebase' parent='Knowledgebase' title='Knowledgebase' />
      <Container fluid={true} className='faq-section'>
        <Row>
          <HeaderPart />
          <Articals />
          <BrowseArticlesClass />
          <Col lg='12' className='featured-tutorial'>
            <div className='header-faq'>
              <H5>Featured Tutorials</H5>
            </div>
            <FeaturesTutorial />
          </Col>
          <LatestArticlesClass />
        </Row>
      </Container>
    </Fragment>
  );
};
export default KnowledgeBaseContain;
