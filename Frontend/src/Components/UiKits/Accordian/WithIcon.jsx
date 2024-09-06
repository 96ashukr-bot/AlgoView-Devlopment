import React, { useState } from 'react';
import { Accordion, Col } from 'react-bootstrap';
import { Card, CardBody, CardHeader, Collapse } from 'reactstrap';
import { Btn, H5 } from '../../../AbstractElements';
import { AllCloseAccordion, CollapsibleGroupItem } from '../../../Constant';

const WithIcon = () => {
  const [isOpen, setIsOpen] = useState(1);
  const toggle = (id) => (isOpen === id ? setIsOpen(null) : setIsOpen(id));
  const data = [
    {
      id: 2,
      icon: 'icofont-support'
    },
    {
      id: 3,
      icon: 'icofont-tasks-alt'
    },
  ];
  return (
    <Col sm="12" xl="6">
      <Accordion defaultActiveKey="0">
        <Card>
          <CardHeader>
            <H5>{AllCloseAccordion}</H5><span>{'Using the'} <a href="#javascript">{'card'}</a> {'component, you can extend the default collapse behavior to create an accordion.'}</span>
          </CardHeader>
          <CardBody>
            <div className="default-according" id="accordion1">
              <Card>
                <CardHeader className="bg-primary">
                  <H5 attrH5={{ className: 'mb-0' }} >
                    <Btn attrBtn={{ as: Card.Header, className: 'btn btn-link text-white', color: 'default', onClick: () => toggle(1) }} >
                      <i className="icofont icofont-briefcase-alt-2"></i>{CollapsibleGroupItem}<span className="digits">1</span>
                    </Btn>
                  </H5>
                </CardHeader>
                <Collapse isOpen={isOpen === 1}>
                  <CardBody>
                    {'Anim pariatur cliche reprehenderit, enim eiusmod high life accusamus terry richardson ad squid. 3 wolf moon officia aute, non cupidatat skateboard dolor brunch. Food truck quinoa nesciunt laborum eiusmod. Brunch 3 wolf moon tempor, sunt aliqua put a bird on it squid single-origin coffee nulla assumenda shoreditch et. Nihil anim keffiyeh helvetica, craft beer labore wes anderson cred nesciunt sapiente ea proident. Ad vegan excepteur butcher vice lomo. Leggings occaecat craft beer farm-to-table, raw denim aesthetic synth nesciunt you probably haven\'t heard of them accusamus labore sustainable VHS.'}
                  </CardBody>
                </Collapse>
              </Card>
              {data.map((accordian, i) =>
                <Card key={i}>
                  <CardHeader className="bg-primary">
                    <H5 attrH5={{ className: 'mb-0' }} >
                      <Btn attrBtn={{ as: Card.Header, className: 'btn btn-link text-white', color: 'default', onClick: () => toggle(accordian.id) }} >
                        <i className={`icofont ${accordian.icon}`}></i>{CollapsibleGroupItem}<span className="digits">{accordian.id}</span>
                      </Btn>
                    </H5>
                  </CardHeader>
                  <Collapse isOpen={isOpen === accordian.id}>
                    <CardBody>
                      {'Anim pariatur cliche reprehenderit, enim eiusmod high life accusamus terry richardson ad squid. 3 wolf moon officia aute, non cupidatat skateboard dolor brunch. Food truck quinoa nesciunt laborum eiusmod. Brunch 3 wolf moon tempor, sunt aliqua put a bird on it squid single-origin coffee nulla assumenda shoreditch et. Nihil anim keffiyeh helvetica, craft beer labore wes anderson cred nesciunt sapiente ea proident. Ad vegan excepteur butcher vice lomo. Leggings occaecat craft beer farm-to-table, raw denim aesthetic synth nesciunt you probably haven\'t heard of them accusamus labore sustainable VHS.'}
                    </CardBody>
                  </Collapse>
                </Card>
              )}
            </div>
          </CardBody>
        </Card>
      </Accordion>
    </Col>
  );
};

export default WithIcon;