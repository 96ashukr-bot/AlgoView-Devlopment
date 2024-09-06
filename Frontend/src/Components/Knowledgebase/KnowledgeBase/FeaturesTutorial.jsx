import React, { Fragment, useContext } from 'react';
import { H6, Image, LI, P, UL } from '../../../AbstractElements';
import LearningContext from '../../../_helper/Learning';
import { Download, Link } from 'react-feather';
import { NavLink } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';
import { Card, CardBody, CardFooter, Col, Row } from 'reactstrap';
import CustomizerContext from '../../../_helper/Customizer';

const FeaturesTutorial = () => {
  const { layoutURL } = useContext(CustomizerContext);

  const { learningData } = useContext(LearningContext);
  const history = useNavigate();
  const clickApply = () => {
    history(`/app/knowledgebase-detail/${layoutURL}`);
  };
  var images = require.context('../../../assets/images', true);
  const dynamicImage = (image) => {
    return images(`./${image}`);
  };
  return (
    <Fragment>
      <Row>
        {learningData &&
          learningData.slice(0, 4).map((item) => {
            return (
              <Col xl='3' md='6' key={item.Id} className='xl-50 box-col-6'>
                <Card className='features-faq product-box'>
                  <div className='faq-image product-img'>
                    <Image attrImage={{ className: 'img-fluid', src: `${dynamicImage(item.img)}`, alt: '' }} />
                    <div className='product-hover'>
                      <UL attrUL={{ className: 'simple-list flex-row' }}>
                        <LI attrLI={{ className: 'border-0' }}>
                          <Link onClick={clickApply} />
                        </LI>
                        <LI attrLI={{ className: 'border-0' }}>
                          <Download />
                        </LI>
                      </UL>
                    </div>
                  </div>
                  <CardBody>
                    <H6>
                      <NavLink to={`/app/knowledgebase-detail/${layoutURL}`}>{item.title}</NavLink>
                    </H6>
                    <P>{item.short_description}</P>
                  </CardBody>
                  <CardFooter>
                    <span>{item.date}</span>
                    <span className='pull-right'>
                      <i className='fa fa-star font-primary'></i>
                      <i className='fa fa-star font-primary'></i>
                      <i className='fa fa-star font-primary'></i>
                      <i className='fa fa-star font-primary'></i>
                      <i className='fa fa-star font-primary'></i>
                    </span>
                  </CardFooter>
                </Card>
              </Col>
            );
          })}
      </Row>
    </Fragment>
  );
};
export default FeaturesTutorial;
