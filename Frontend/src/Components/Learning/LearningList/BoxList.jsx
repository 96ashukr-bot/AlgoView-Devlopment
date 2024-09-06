import { Image, LI, UL } from '../../../AbstractElements';
import LearningContext from '../../../_helper/Learning';
import React, { Fragment, useContext } from 'react';
import { Col, Card } from 'reactstrap';
import { useNavigate } from 'react-router-dom';
import CustomizerContext from '../../../_helper/Customizer';

const BoxList = () => {
  const { layoutURL } = useContext(CustomizerContext);
  const { learningData } = useContext(LearningContext);

  const history = useNavigate();
  const clickApply = () => {
    history(`/app/learning/learningdetail/${layoutURL}`);
  };

  return (
    <Fragment>
      {learningData &&
        learningData.map((data, i) => {
          return (
            <Col xl='4' sm='6' key={i} className='xl-50 box-col-6'>
              <Card>
                <div className='blog-box blog-grid product-box text-center learning-box'>
                  <div className='product-img'>
                    <Image attrImage={{ className: 'img-fluid top-radius-blog', src: `${require('../../../assets/images/' + data.img)}`, alt: '' }} />
                    <div className='product-hover'>
                      <UL attrUL={{ className: 'flex-row' }}>
                        <LI>
                          <i className='icon-link' onClick={() => clickApply()}></i>
                        </LI>
                        <LI>
                          <i className='icon-import'></i>
                        </LI>
                      </UL>
                    </div>
                  </div>
                  <div className='blog-details-main'>
                    <ul className='blog-social'>
                      <li>{data.date}</li>
                      <li>{data.writer}</li>
                      <li>Hits : {data.hits}</li>
                    </ul>
                    <hr />
                    <h6 className='blog-bottom-details'>{data.short_description}</h6>
                  </div>
                </div>
              </Card>
            </Col>
          );
        })}
    </Fragment>
  );
};

export default BoxList;
