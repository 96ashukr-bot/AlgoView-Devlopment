import React, { Fragment, useState, useEffect } from 'react';
import { Breadcrumbs } from '../../../AbstractElements';
import IconMarkUp from '../Icon-markup';
import { Container, Row, Col, Card, CardHeader, CardBody, Media } from 'reactstrap';
import axios from 'axios';
import { FlagIcons } from '../../../Constant';
import { FlagIconDataApi } from '../../../api';

const FlagIcon = () => {
  const [iTag, setITag] = useState('');
  const [iconsData, setIconsData] = useState([]);
  const [icon, setIcon] = useState('');

  useEffect(() => {
    axios.get(FlagIconDataApi).then((res) => setIconsData(res.data));
  }, []);

  const getItag = (tag) => {
    setITag({
      iTag: '<i className="flag-icon flag-icon-' + tag + '"></i>',
    });
    setIcon({
      icon: 'flag-icon flag-icon-' + tag + ' fa-2x',
    });
  };

  return (
    <Fragment>
      <Breadcrumbs mainTitle='Flag Icons' parent='Icons' title='Flag Icons' />
      <Container fluid={true}>
        <Row>
          <Col sm='12'>
            <Card>
              <CardHeader>
                <h5 className='m-b-0'>{FlagIcons}</h5>
              </CardHeader>
              <CardBody>
                <Row className='icon-lists flag-icons'>
                  {iconsData.map((icon, i) => {
                    return (
                      <Col sm='6 col-12' xl='4' key={i} onClick={(e) => getItag(icon.abbrivation)}>
                        <Media>
                          <i className={`flag-icon flag-icon-${icon.abbrivation}`}></i>
                          <Media body className='align-self-center'>
                            <h5>{icon.abbrivation}</h5>
                            <h6 className='mt-0'>{icon.name}</h6>
                          </Media>
                        </Media>
                      </Col>
                    );
                  })}
                </Row>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
      <IconMarkUp itag={iTag} icons={icon} />
    </Fragment>
  );
};

export default FlagIcon;
