import React from 'react';
import { Card, CardBody, Col, Table } from 'reactstrap';
import { P } from '../../../../AbstractElements';
import { ColumnOrdering, ExtraLarge,ExtraextraLarge, ExtraSmall, GridBehavior, GridOptions, GutterWidth, Large, Medium, Nestable, Offsets, Small } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const GridOptionsCard = () => {
  return (
    <Col sm="12">
      <Card>
        <HeaderCard title={GridOptions} span1='Bootstrap grid allows building an equal height flexbile blocks easily' />
        <CardBody>
          <P>{'While Bootstrap uses'} <code>{'em'} </code>{'or'} <code>{'rem'} </code>{'for defining most sizes'}, <code>{'px'}</code> {'are used for grid breakpoints and container widths. This is because the viewport width is in pixels and does not change with the'} <a href="#javascript">{'font size'}</a>.</P>
          <div className="table-responsive">
            <Table bordered striped>
              <thead>
                <tr>
                  <th></th>
                  <th className="text-center">{ExtraSmall}<br /><small className="digits">&lt;{'576px'}</small></th>
                  <th className="text-center">{Small}<br /><small className="digits">{'≥576px'}</small></th>
                  <th className="text-center">{Medium}<br /><small className="digits">{'≥768px'}</small></th>
                  <th className="text-center">{Large}<br /><small className="digits">{'≥992px'}</small></th>
                  <th className="text-center">{ExtraLarge}<br /><small className="digits">{'≥1200px'}</small></th>
                  <th className="text-center">{ExtraextraLarge}<br /><small className="digits">{'≥1400px'}</small></th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th className="text-nowrap" scope="row">{GridBehavior}</th>
                  <td>{'Horizontal at all times'}</td>
                  <td colSpan={5}>{'Collapsed to start, horizontal above breakpoints'}</td>
                </tr>
                <tr>
                  <th className="text-nowrap" scope="row">{'Max container width'}</th>
                  <td>{'None (auto)'}</td>
                  <td className="digits">{'540px'}</td>
                  <td className="digits">{'720px'}</td>
                  <td className="digits">{'960px'}</td>
                  <td className="digits">{'1140px'}</td>
                  <td className="digits">{'1320px'}</td>
                </tr>
                <tr>
                  <th className="text-nowrap" scope="row">{'className prefix'}</th>
                  <td><code>{'.col-'}</code></td>
                  <td><code>{'.col-sm-'}</code></td>
                  <td><code>{'.col-md-'}</code></td>
                  <td><code>{'.col-lg-'}</code></td>
                  <td><code>{'.col-xl-'}</code></td>
                  <td><code>{'.col-xxl-'}</code></td>
                </tr>
                <tr>
                  <th className="text-nowrap" scope="row">{'# of columns'}</th>
                  <td colSpan={6}>{'12'}</td>
                </tr>
                <tr>
                  <th className="text-nowrap" scope="row">{GutterWidth}</th>
                  <td colSpan={6}>{'30px (15px on each side of a column)'}</td>
                </tr>
                <tr>
                  <th className="text-nowrap" scope="row">{Nestable}</th>
                  <td colSpan={6}>{'Yes'}</td>
                </tr>
                <tr>
                  <th className="text-nowrap" scope="row">{Offsets}</th>
                  <td colSpan={6}>{'Yes'}</td>
                </tr>
                <tr>
                  <th className="text-nowrap" scope="row">{ColumnOrdering}</th>
                  <td colSpan={6}>{'Yes'}</td>
                </tr>
              </tbody>
            </Table>
          </div>
        </CardBody>
      </Card>
    </Col>
  );
};

export default GridOptionsCard;