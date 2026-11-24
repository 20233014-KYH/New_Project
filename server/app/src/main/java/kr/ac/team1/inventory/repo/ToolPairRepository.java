package kr.ac.team1.inventory.repo;

import java.util.Optional;
import kr.ac.team1.inventory.domain.ToolPair;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ToolPairRepository extends JpaRepository<ToolPair, Long> {

    Optional<ToolPair> findByPairKey(String pairKey);
}
