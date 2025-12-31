#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Procedure Graph Builder - Xây dựng đồ thị mối quan hệ giữa các thủ tục hành chính

Phát hiện và lưu trữ các mối quan hệ:
1. Same Domain: Cùng lĩnh vực (e.g., "Chính sách", "Ứng phó sự cố tràn dầu")
2. Related Legal: Cùng căn cứ pháp lý
3. Sequential Flow: Thủ tục liên tiếp (output của A là input của B)
4. Similar Content: Nội dung tương tự (semantic similarity)

Output: Graph structure với adjacency list để enrichment trong retrieval
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict
import re

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class ProcedureNode:
    """Node representing a single procedure"""
    thu_tuc_id: str
    ten_thu_tuc: str
    linh_vuc: str
    cap_thuc_hien: str
    loai_thu_tuc: str

    # References for relationship detection
    legal_basis_ids: List[str]  # List of legal document IDs
    required_documents: List[str]  # Input documents
    result_documents: List[str]  # Output documents
    keywords: List[str]  # For semantic matching


@dataclass
class ProcedureRelationship:
    """Edge representing relationship between 2 procedures"""
    from_id: str
    to_id: str
    relationship_type: str  # "same_domain", "related_legal", "sequential", "similar"
    strength: float  # 0.0 - 1.0
    metadata: Dict  # Additional context


class ProcedureGraph:
    """
    Graph-based structure for procedure relationships

    Usage:
        graph = ProcedureGraph()
        graph.load_procedures("data/extracted_fixed")
        graph.build_relationships()
        graph.save("data/procedure_graph.json")
    """

    def __init__(self):
        self.nodes: Dict[str, ProcedureNode] = {}
        self.relationships: List[ProcedureRelationship] = []
        self.adjacency_list: Dict[str, List[str]] = defaultdict(list)

        # Domain groupings for quick lookup
        self.domain_groups: Dict[str, List[str]] = defaultdict(list)
        self.legal_basis_index: Dict[str, List[str]] = defaultdict(list)

    def load_procedures(self, extracted_dir: Path):
        """
        Load all procedures from extracted JSON files

        Args:
            extracted_dir: Path to directory containing extracted procedure JSONs
        """
        extracted_dir = Path(extracted_dir)
        json_files = sorted(extracted_dir.glob("*.json"))

        print(f"📂 Loading procedures from {extracted_dir}")
        print(f"   Found {len(json_files)} procedure files")
        print()

        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract node information
            node = self._create_node_from_data(data)
            self.nodes[node.thu_tuc_id] = node

            # Build indexes
            self.domain_groups[node.linh_vuc].append(node.thu_tuc_id)
            for legal_id in node.legal_basis_ids:
                self.legal_basis_index[legal_id].append(node.thu_tuc_id)

        print(f"✅ Loaded {len(self.nodes)} procedure nodes")
        print(f"✅ Found {len(self.domain_groups)} unique domains")
        print(f"✅ Indexed {len(self.legal_basis_index)} unique legal documents")
        print()

    def _create_node_from_data(self, data: Dict) -> ProcedureNode:
        """Create ProcedureNode from extracted JSON data"""
        metadata = data.get("metadata", {})
        content = data.get("content", {})
        tables = data.get("tables", {})

        # Extract legal basis IDs
        legal_basis_ids = []
        for legal in tables.get("can_cu_phap_ly", []):
            so_ky_hieu = legal.get("so_ky_hieu", "").strip()
            if so_ky_hieu:
                # Normalize: "12/2021/QĐ-TTg" -> "12_2021_QD_TTg"
                normalized_id = re.sub(r'[/\-]', '_', so_ky_hieu)
                legal_basis_ids.append(normalized_id)

        # Extract required documents (input)
        required_docs = []
        for doc in tables.get("thanh_phan_ho_so", []):
            ten_giay_to = doc.get("ten_giay_to", "").strip()
            if ten_giay_to:
                required_docs.append(ten_giay_to)

        # Extract result documents (output)
        result_docs = []
        ket_qua = content.get("kết_quả_thực_hiện", "").strip()
        if ket_qua and ket_qua != "Không có thông tin":
            result_docs.append(ket_qua)

        # Extract keywords
        keywords = []
        tu_khoa = content.get("từ_khóa", "").strip()
        if tu_khoa and tu_khoa != "Không có thông tin":
            # Split by comma or semicolon
            keywords = [k.strip() for k in re.split(r'[,;]', tu_khoa) if k.strip()]

        # Add domain as keyword
        linh_vuc = metadata.get("lĩnh_vực", "").strip()
        if linh_vuc:
            keywords.append(linh_vuc)

        return ProcedureNode(
            thu_tuc_id=data["thu_tuc_id"],
            ten_thu_tuc=metadata.get("tên_thủ_tục", ""),
            linh_vuc=linh_vuc,
            cap_thuc_hien=metadata.get("cấp_thực_hiện", ""),
            loai_thu_tuc=metadata.get("loại_thủ_tục", ""),
            legal_basis_ids=legal_basis_ids,
            required_documents=required_docs,
            result_documents=result_docs,
            keywords=keywords
        )

    def build_relationships(self):
        """
        Build all relationship types between procedures

        Creates 4 types of relationships:
        1. Same Domain (high priority for retrieval)
        2. Related Legal Basis (shared legal foundation)
        3. Sequential Flow (output -> input matching)
        4. Similar Content (keyword overlap)
        """
        print("🔗 Building relationships between procedures...")
        print()

        # 1. Same Domain relationships
        self._build_domain_relationships()

        # 2. Related Legal Basis relationships
        self._build_legal_relationships()

        # 3. Sequential Flow relationships
        self._build_sequential_relationships()

        # 4. Similar Content relationships
        self._build_similarity_relationships()

        # Build adjacency list for quick lookup
        self._build_adjacency_list()

        print(f"✅ Created {len(self.relationships)} total relationships")
        print()

    def _build_domain_relationships(self):
        """Create relationships between procedures in same domain"""
        count = 0

        for domain, procedure_ids in self.domain_groups.items():
            if len(procedure_ids) < 2:
                continue

            # Create bidirectional relationships within domain
            for i, id1 in enumerate(procedure_ids):
                for id2 in procedure_ids[i+1:]:
                    # High strength for same domain
                    self.relationships.append(ProcedureRelationship(
                        from_id=id1,
                        to_id=id2,
                        relationship_type="same_domain",
                        strength=0.8,
                        metadata={"domain": domain}
                    ))

                    # Bidirectional
                    self.relationships.append(ProcedureRelationship(
                        from_id=id2,
                        to_id=id1,
                        relationship_type="same_domain",
                        strength=0.8,
                        metadata={"domain": domain}
                    ))
                    count += 2

        print(f"   ✅ Domain: {count} relationships")

    def _build_legal_relationships(self):
        """Create relationships between procedures sharing legal basis"""
        count = 0

        for legal_id, procedure_ids in self.legal_basis_index.items():
            if len(procedure_ids) < 2:
                continue

            # Create bidirectional relationships for shared legal basis
            for i, id1 in enumerate(procedure_ids):
                for id2 in procedure_ids[i+1:]:
                    # Medium-high strength for shared legal basis
                    self.relationships.append(ProcedureRelationship(
                        from_id=id1,
                        to_id=id2,
                        relationship_type="related_legal",
                        strength=0.7,
                        metadata={"legal_basis": legal_id}
                    ))

                    self.relationships.append(ProcedureRelationship(
                        from_id=id2,
                        to_id=id1,
                        relationship_type="related_legal",
                        strength=0.7,
                        metadata={"legal_basis": legal_id}
                    ))
                    count += 2

        print(f"   ✅ Legal: {count} relationships")

    def _build_sequential_relationships(self):
        """
        Create sequential relationships where output of A is input of B

        Example: "Giấy chứng nhận đăng ký" (output of A) -> required by B
        """
        count = 0

        # Build a reverse index: result_doc -> procedure_ids that produce it
        result_index: Dict[str, List[str]] = defaultdict(list)
        for node in self.nodes.values():
            for result_doc in node.result_documents:
                # Normalize document name
                normalized = self._normalize_document_name(result_doc)
                result_index[normalized].append(node.thu_tuc_id)

        # Check if any procedure's required docs match another's results
        for node in self.nodes.values():
            for required_doc in node.required_documents:
                normalized = self._normalize_document_name(required_doc)

                # Find procedures that produce this document
                producing_procedures = result_index.get(normalized, [])

                for producer_id in producing_procedures:
                    if producer_id != node.thu_tuc_id:
                        # Sequential: producer -> consumer
                        self.relationships.append(ProcedureRelationship(
                            from_id=producer_id,
                            to_id=node.thu_tuc_id,
                            relationship_type="sequential",
                            strength=0.9,  # High strength for direct flow
                            metadata={"document": required_doc}
                        ))
                        count += 1

        print(f"   ✅ Sequential: {count} relationships")

    def _build_similarity_relationships(self):
        """
        Create similarity relationships based on keyword overlap

        Uses Jaccard similarity on keywords
        """
        count = 0
        threshold = 0.3  # Minimum Jaccard similarity

        node_list = list(self.nodes.values())

        for i, node1 in enumerate(node_list):
            if not node1.keywords:
                continue

            for node2 in node_list[i+1:]:
                if not node2.keywords:
                    continue

                # Calculate Jaccard similarity
                set1 = set(node1.keywords)
                set2 = set(node2.keywords)

                intersection = len(set1 & set2)
                union = len(set1 | set2)

                if union > 0:
                    similarity = intersection / union

                    if similarity >= threshold:
                        # Bidirectional similarity
                        self.relationships.append(ProcedureRelationship(
                            from_id=node1.thu_tuc_id,
                            to_id=node2.thu_tuc_id,
                            relationship_type="similar",
                            strength=similarity,
                            metadata={
                                "shared_keywords": list(set1 & set2),
                                "jaccard_score": similarity
                            }
                        ))

                        self.relationships.append(ProcedureRelationship(
                            from_id=node2.thu_tuc_id,
                            to_id=node1.thu_tuc_id,
                            relationship_type="similar",
                            strength=similarity,
                            metadata={
                                "shared_keywords": list(set1 & set2),
                                "jaccard_score": similarity
                            }
                        ))
                        count += 2

        print(f"   ✅ Similar: {count} relationships")

    def _normalize_document_name(self, doc_name: str) -> str:
        """
        Normalize document name for matching

        Example: "Giấy chứng nhận đăng ký kinh doanh" -> "giay_chung_nhan_dang_ky_kinh_doanh"
        """
        # Remove special characters, lowercase, replace spaces with underscore
        normalized = re.sub(r'[^\w\s]', '', doc_name.lower())
        normalized = re.sub(r'\s+', '_', normalized.strip())
        return normalized

    def _build_adjacency_list(self):
        """Build adjacency list for quick neighbor lookup"""
        for rel in self.relationships:
            self.adjacency_list[rel.from_id].append(rel.to_id)

    def get_related_procedures(
        self,
        thu_tuc_id: str,
        relationship_types: List[str] = None,
        min_strength: float = 0.0,
        max_results: int = 10
    ) -> List[Tuple[str, ProcedureRelationship]]:
        """
        Get related procedures for a given procedure

        Args:
            thu_tuc_id: Source procedure ID
            relationship_types: Filter by types (None = all types)
            min_strength: Minimum relationship strength
            max_results: Maximum number of results

        Returns:
            List of (related_id, relationship) tuples, sorted by strength
        """
        related = []

        for rel in self.relationships:
            if rel.from_id != thu_tuc_id:
                continue

            # Filter by type
            if relationship_types and rel.relationship_type not in relationship_types:
                continue

            # Filter by strength
            if rel.strength < min_strength:
                continue

            related.append((rel.to_id, rel))

        # Sort by strength (descending)
        related.sort(key=lambda x: x[1].strength, reverse=True)

        return related[:max_results]

    def save(self, output_path: Path):
        """
        Save graph to JSON file

        Format:
        {
            "nodes": {...},
            "relationships": [...],
            "adjacency_list": {...},
            "statistics": {...}
        }
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to serializable format
        graph_data = {
            "nodes": {
                node_id: asdict(node)
                for node_id, node in self.nodes.items()
            },
            "relationships": [
                asdict(rel) for rel in self.relationships
            ],
            "adjacency_list": dict(self.adjacency_list),
            "statistics": {
                "total_nodes": len(self.nodes),
                "total_relationships": len(self.relationships),
                "total_domains": len(self.domain_groups),
                "relationship_types": self._get_relationship_stats()
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)

        print(f"💾 Saved procedure graph to: {output_path}")
        print(f"   Nodes: {len(self.nodes)}")
        print(f"   Relationships: {len(self.relationships)}")

    def _get_relationship_stats(self) -> Dict[str, int]:
        """Get statistics on relationship types"""
        stats = defaultdict(int)
        for rel in self.relationships:
            stats[rel.relationship_type] += 1
        return dict(stats)

    @classmethod
    def load(cls, graph_path: Path) -> 'ProcedureGraph':
        """
        Load graph from JSON file

        Args:
            graph_path: Path to saved graph JSON

        Returns:
            ProcedureGraph instance
        """
        with open(graph_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        graph = cls()

        # Restore nodes
        for node_id, node_data in data["nodes"].items():
            graph.nodes[node_id] = ProcedureNode(**node_data)

        # Restore relationships
        for rel_data in data["relationships"]:
            graph.relationships.append(ProcedureRelationship(**rel_data))

        # Restore adjacency list
        graph.adjacency_list = defaultdict(list, data["adjacency_list"])

        # Rebuild indexes
        for node in graph.nodes.values():
            graph.domain_groups[node.linh_vuc].append(node.thu_tuc_id)
            for legal_id in node.legal_basis_ids:
                graph.legal_basis_index[legal_id].append(node.thu_tuc_id)

        print(f"✅ Loaded procedure graph from: {graph_path}")
        print(f"   Nodes: {len(graph.nodes)}")
        print(f"   Relationships: {len(graph.relationships)}")

        return graph


def main():
    """Build procedure graph from extracted data"""
    print("=" * 80)
    print("PROCEDURE GRAPH BUILDER")
    print("=" * 80)
    print()

    # Paths
    extracted_dir = Path("data/extracted_fixed")
    output_path = Path("data/procedure_graph.json")

    # Build graph
    graph = ProcedureGraph()
    graph.load_procedures(extracted_dir)
    graph.build_relationships()
    graph.save(output_path)

    print()
    print("=" * 80)
    print("📊 STATISTICS")
    print("=" * 80)

    # Domain distribution
    print("\n🏢 Procedures by Domain:")
    for domain, ids in sorted(graph.domain_groups.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"   {domain}: {len(ids)} procedures")

    # Relationship type distribution
    print("\n🔗 Relationships by Type:")
    stats = graph._get_relationship_stats()
    for rel_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        print(f"   {rel_type}: {count} relationships")

    print()
    print("=" * 80)
    print("✅ DONE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
