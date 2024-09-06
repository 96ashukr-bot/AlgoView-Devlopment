import React, { Fragment, useCallback, useState } from 'react';
import { CardBody, CardHeader, Form, Input, Row, Col, Card, Container, TabContent, TabPane } from 'reactstrap';
import AllTabs from './AllTabs';
import ImageTabs from './ImageTabs';
import SearchTabs from './SearchTabs';
import VideoTabs from './VideoTabs';
import { Breadcrumbs } from '../../../AbstractElements';

const SearchResultContain = () => {
  const [activeTab, setActiveTab] = useState('1');
  const callback = useCallback(
    (tab) => {
      setActiveTab(tab);
    },
    [activeTab],
  );
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Search Result' parent='Apps' title='Search Result' />
      <Container fluid={true} className='search-page'>
        <Row>
          <Col sm='12'>
            <Card>
              <CardHeader>
                <Form className='theme-form'>
                  <div className='input-group flex-nowrap'>
                    <Input className='form-control-plaintext' type='search' placeholder='Search..' />
                    <span className='btn btn-primary input-group-text'>Search</span>
                  </div>
                </Form>
              </CardHeader>
              <CardBody>
                <SearchTabs callbackActive={callback} />
                <TabContent activeTab={activeTab} className='tab-content'>
                  <TabPane tabId='1'>
                    <AllTabs />
                  </TabPane>
                  <TabPane tabId='2'>
                    <ImageTabs />
                  </TabPane>
                  <TabPane tabId='3'>
                    <VideoTabs />
                  </TabPane>
                  <TabPane tabId='4'></TabPane>
                  <TabPane tabId='5'></TabPane>
                </TabContent>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};
export default SearchResultContain;
