/**
 * Structured procedure data display component
 */

import { useState } from 'react';
import { ChevronDownIcon } from '../common/Icons';
import type { StructuredData } from '../../services/types';
import './StructuredProcedure.css';

interface StructuredProcedureProps {
  data: StructuredData;
}

export const StructuredProcedure = ({ data }: StructuredProcedureProps) => {
  const [openSections, setOpenSections] = useState<Set<string>>(new Set(['metadata']));

  const toggleSection = (section: string) => {
    setOpenSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  const renderTable = (tableData: Array<{ [key: string]: string }>) => {
    if (!tableData || tableData.length === 0) return null;

    const headers = Object.keys(tableData[0]);

    return (
      <div className="structured-procedure__table-wrapper">
        <table className="structured-procedure__table">
          <thead>
            <tr>
              {headers.map((header) => (
                <th key={header}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tableData.map((row, idx) => (
              <tr key={idx}>
                {headers.map((header) => (
                  <td key={header}>{row[header]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="structured-procedure">
      <h4 className="structured-procedure__title">Thông tin chi tiết thủ tục</h4>

      {/* Metadata Section */}
      {data.metadata && (
        <details
          className="structured-procedure__section"
          open={openSections.has('metadata')}
          onToggle={() => toggleSection('metadata')}
        >
          <summary className="structured-procedure__section-header">
            <span>Thông tin chung</span>
            <ChevronDownIcon />
          </summary>
          <div className="structured-procedure__section-content">
            <dl className="structured-procedure__list">
              {data.metadata.mã_thủ_tục && (
                <>
                  <dt>Mã thủ tục:</dt>
                  <dd className="structured-procedure__code">
                    {data.metadata.mã_thủ_tục}
                  </dd>
                </>
              )}
              {data.metadata.tên_thủ_tục && (
                <>
                  <dt>Tên thủ tục:</dt>
                  <dd><strong>{data.metadata.tên_thủ_tục}</strong></dd>
                </>
              )}
              {data.metadata.cấp_thực_hiện && (
                <>
                  <dt>Cấp thực hiện:</dt>
                  <dd>{data.metadata.cấp_thực_hiện}</dd>
                </>
              )}
              {data.metadata.lĩnh_vực && (
                <>
                  <dt>Lĩnh vực:</dt>
                  <dd>{data.metadata.lĩnh_vực}</dd>
                </>
              )}
              {data.metadata.loại_thủ_tục && (
                <>
                  <dt>Loại thủ tục:</dt>
                  <dd>{data.metadata.loại_thủ_tục}</dd>
                </>
              )}
            </dl>
          </div>
        </details>
      )}

      {/* Content Section */}
      {data.content && Object.keys(data.content).length > 0 && (
        <details
          className="structured-procedure__section"
          open={openSections.has('content')}
          onToggle={() => toggleSection('content')}
        >
          <summary className="structured-procedure__section-header">
            <span>Nội dung thủ tục</span>
            <ChevronDownIcon />
          </summary>
          <div className="structured-procedure__section-content">
            <dl className="structured-procedure__list">
              {data.content.trình_tự_thực_hiện && (
                <>
                  <dt>Trình tự thực hiện:</dt>
                  <dd>{data.content.trình_tự_thực_hiện}</dd>
                </>
              )}
              {data.content.đối_tượng_thực_hiện && (
                <>
                  <dt>Đối tượng thực hiện:</dt>
                  <dd>{data.content.đối_tượng_thực_hiện}</dd>
                </>
              )}
              {data.content.cơ_quan_thực_hiện && (
                <>
                  <dt>Cơ quan thực hiện:</dt>
                  <dd>{data.content.cơ_quan_thực_hiện}</dd>
                </>
              )}
              {data.content.kết_quả_thực_hiện && (
                <>
                  <dt>Kết quả thực hiện:</dt>
                  <dd>{data.content.kết_quả_thực_hiện}</dd>
                </>
              )}
              {data.content.thời_gian_giải_quyết && (
                <>
                  <dt>Thời gian giải quyết:</dt>
                  <dd>{data.content.thời_gian_giải_quyết}</dd>
                </>
              )}
              {data.content.phí_lệ_phí && (
                <>
                  <dt>Phí, lệ phí:</dt>
                  <dd>{data.content.phí_lệ_phí}</dd>
                </>
              )}
              {data.content.địa_điểm_thực_hiện && (
                <>
                  <dt>Địa điểm thực hiện:</dt>
                  <dd>{data.content.địa_điểm_thực_hiện}</dd>
                </>
              )}
            </dl>
          </div>
        </details>
      )}

      {/* Tables Section */}
      {data.tables && (
        <>
          {data.tables.thanh_phan_ho_so && data.tables.thanh_phan_ho_so.length > 0 && (
            <details
              className="structured-procedure__section"
              open={openSections.has('ho_so')}
              onToggle={() => toggleSection('ho_so')}
            >
              <summary className="structured-procedure__section-header">
                <span>Thành phần hồ sơ</span>
                <ChevronDownIcon />
              </summary>
              <div className="structured-procedure__section-content">
                {renderTable(data.tables.thanh_phan_ho_so)}
              </div>
            </details>
          )}

          {data.tables.hinh_thuc_nop && data.tables.hinh_thuc_nop.length > 0 && (
            <details
              className="structured-procedure__section"
              open={openSections.has('hinh_thuc')}
              onToggle={() => toggleSection('hinh_thuc')}
            >
              <summary className="structured-procedure__section-header">
                <span>Hình thức nộp</span>
                <ChevronDownIcon />
              </summary>
              <div className="structured-procedure__section-content">
                {renderTable(data.tables.hinh_thuc_nop)}
              </div>
            </details>
          )}

          {data.tables.can_cu_phap_ly && data.tables.can_cu_phap_ly.length > 0 && (
            <details
              className="structured-procedure__section"
              open={openSections.has('phap_ly')}
              onToggle={() => toggleSection('phap_ly')}
            >
              <summary className="structured-procedure__section-header">
                <span>Căn cứ pháp lý</span>
                <ChevronDownIcon />
              </summary>
              <div className="structured-procedure__section-content">
                {renderTable(data.tables.can_cu_phap_ly)}
              </div>
            </details>
          )}
        </>
      )}
    </div>
  );
};
